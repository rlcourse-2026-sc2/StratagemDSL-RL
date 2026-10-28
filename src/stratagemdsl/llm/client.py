"""
Real LLM client for StratagemDSL variant generation.

Two call paths, both asking for one call of the emit_stratagem_variant tool:
  - Anthropic (Claude): the anthropic SDK, streamed.  Current Claude models
    reject a forced tool_choice and sampling parameters, so those are dropped
    on rejection and the answer falls back to JSON in text.
  - Everything else (OpenAI, DeepSeek, GLM/Qwen/Moonshot, Ollama, relays):
    the `openai` SDK's function calling, with the same drop-and-retry for
    temperature / max_tokens naming / forced tool_choice.

`ProviderConfig` intentionally has the exact same field names as smac-ast's
`sc2_map_forge.services.ProviderConfig` so a caller can pass that object
straight through without any adapting.

No network egress to any LLM provider is reachable from the sandbox this
code was written in, so the two `_call_*` functions below are untested
against a live endpoint. Everything upstream/downstream of them (schema,
prompt construction, response parsing, repair loop, and the full
parse->validate->lower->compile pipeline) is fully tested with a
hand-built mock response in `stratagemdsl/tests`.
"""
from __future__ import annotations

import json
import sys
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

from stratagemdsl.registry.schema import StrategyS, strategy_json_schema
from stratagemdsl.core.model import Strategy

TOOL_NAME = "emit_stratagem_variant"
TOOL_DESCRIPTION = (
    "Emit one complete StratagemDSL strategy (world, initial state, intent, "
    "derived facts, reactive plan graph, and sc2 backend binding) as structured "
    "data matching the schema exactly."
)


@dataclass
class ProviderConfig:
    key: str
    api_key: str = ""
    base_url: str = ""
    model: str = ""
    # Extra JSON fields merged into OpenAI-compatible request bodies, e.g.
    # {"thinking": {"type": "disabled"}} for DeepSeek V4.
    extra_body: dict = field(default_factory=dict)


# Default output budgets when the caller does not set one.  Thinking models
# (current Claude, DeepSeek V4) count their reasoning against max_tokens.
DEFAULT_MAX_TOKENS = {"anthropic": 32000, "deepseek": 32000}
FALLBACK_MAX_TOKENS = 8096
TOOL_INSTRUCTION = (f"Answer by calling the {TOOL_NAME} tool exactly once with the complete strategy. "
                    "Do not answer in prose.")


def default_max_tokens(provider: ProviderConfig) -> int:
    return DEFAULT_MAX_TOKENS.get(provider.key, FALLBACK_MAX_TOKENS)


def _json_from_text(text: str) -> dict:
    """The first JSON object in a text answer (tolerates ``` fences and prose around it)."""
    start = text.find("{")
    if start < 0:
        raise ValueError("the model answered without calling the tool and without JSON")
    obj, _ = json.JSONDecoder().raw_decode(text[start:])
    return obj


def _mentions(exc: Exception, *words: str) -> bool:
    msg = str(exc).lower()
    return any(w in msg for w in words)


def _stderr_progress(line: str) -> None:
    print(line, file=sys.stderr, flush=True)


# Where "still waiting" lines go; tests and library callers may replace it.
progress: Callable[[str], None] = _stderr_progress
HEARTBEAT_SECONDS = 20.0


class _Heartbeat:
    """Prints how long the model has been working and how much it has sent.

    Thinking models can take minutes before the answer starts; the counters
    show whether the model is still thinking or already writing the answer.
    """

    def __init__(self, model: str):
        self.model, self.thinking, self.answer = model, 0, 0
        self._stop = threading.Event()
        self._start = time.monotonic()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def _run(self):
        while not self._stop.wait(HEARTBEAT_SECONDS):
            elapsed = int(time.monotonic() - self._start)
            state = "thinking" if self.thinking and not self.answer else ("writing" if self.answer else "waiting")
            progress(f"  ... {self.model}: {elapsed} s, {state} (reasoning {self.thinking} chars, "
                     f"answer {self.answer} chars)")

    def __enter__(self):
        self._thread.start()
        return self

    def __exit__(self, *exc):
        self._stop.set()
        return False


def _anthropic_tool_call(provider: ProviderConfig, prompt: str, temperature: float, max_tokens: int) -> dict:
    """Claude through the Anthropic SDK, compatible with old and current models.

    Current models (Opus 5.5 and later) reject a forced tool_choice and any
    sampling parameter, and always think first; older ones accept both.  So the
    call starts with the strictest request and drops what the model refuses:
    temperature (only sent when not the default 1.0), then the forced tool
    choice (replaced by "auto" plus an explicit instruction).  The answer is
    taken from the tool_use block, or from JSON in a text block as a fallback.
    """
    from anthropic import Anthropic

    client = Anthropic(api_key=provider.api_key, **({"base_url": provider.base_url} if provider.base_url else {}))
    kwargs = dict(
        model=provider.model,
        max_tokens=max_tokens,
        system=TOOL_INSTRUCTION,
        tools=[{
            "name": TOOL_NAME,
            "description": TOOL_DESCRIPTION,
            "input_schema": strategy_json_schema(),
        }],
        tool_choice={"type": "tool", "name": TOOL_NAME},
        messages=[{"role": "user", "content": prompt}],
    )
    if temperature is not None and temperature != 1.0:
        kwargs["temperature"] = temperature

    def _run_stream(**stream_kwargs):
        # Streaming, because the SDK refuses blocking requests that may run
        # past 10 minutes; it works the same for short ones.
        with _Heartbeat(provider.model) as beat, client.messages.stream(**stream_kwargs) as stream:
            for event in stream:  # drain; get_final_message() needs the stream fully consumed
                delta = getattr(event, "delta", None)
                if getattr(event, "type", "") == "content_block_delta" and delta is not None:
                    if getattr(delta, "type", "") == "thinking_delta":
                        beat.thinking += len(getattr(delta, "thinking", "") or "")
                    else:
                        beat.answer += len(getattr(delta, "partial_json", "") or getattr(delta, "text", "") or "")
            return stream.get_final_message()

    for _ in range(3):
        try:
            response = _run_stream(**kwargs)
            break
        except Exception as e:  # TypeError from the SDK, or a 400 from the API
            if "temperature" in kwargs and _mentions(e, "temperature", "sampling"):
                kwargs.pop("temperature")
            elif kwargs["tool_choice"]["type"] == "tool" and _mentions(e, "tool_choice", "tool choice"):
                kwargs["tool_choice"] = {"type": "auto"}
            else:
                raise
    else:
        raise RuntimeError("Anthropic request kept being rejected")
    if getattr(response, "stop_reason", None) == "refusal":
        raise RuntimeError("the model refused this request (stop_reason=refusal)")
    for block in response.content:
        if getattr(block, "type", None) == "tool_use":
            return block.input
    text = "".join(getattr(b, "text", "") for b in response.content if getattr(b, "type", None) == "text")
    if getattr(response, "stop_reason", None) == "max_tokens":
        raise RuntimeError(f"output hit max_tokens={max_tokens} before the tool call finished; raise --max-tokens")
    return _json_from_text(text)


def _openai_stream(client, kwargs: dict, model: str) -> tuple[Optional[str], str, Optional[str]]:
    """One streamed chat completion -> (tool call arguments, text content, finish_reason).

    Streaming keeps long thinking runs from hitting read timeouts and feeds
    the heartbeat; endpoints that cannot stream get one blocking call.
    """
    args, content, finish = [], [], None
    try:
        stream = client.chat.completions.create(stream=True, **kwargs)
    except Exception as e:
        if not _mentions(e, "stream"):
            raise
        with _Heartbeat(model):
            response = client.chat.completions.create(**kwargs)
        choice = response.choices[0]
        calls = choice.message.tool_calls or []
        return (calls[0].function.arguments if calls else None), choice.message.content or "", choice.finish_reason
    with _Heartbeat(model) as beat:
        for chunk in stream:
            if not getattr(chunk, "choices", None):
                continue
            choice = chunk.choices[0]
            delta = choice.delta
            reasoning = getattr(delta, "reasoning_content", None) or getattr(delta, "reasoning", None)
            if isinstance(reasoning, str):
                beat.thinking += len(reasoning)
            if getattr(delta, "content", None):
                content.append(delta.content)
                beat.answer += len(delta.content)
            for call in getattr(delta, "tool_calls", None) or []:
                if (call.index or 0) == 0 and call.function and call.function.arguments:
                    args.append(call.function.arguments)
                    beat.answer += len(call.function.arguments)
            finish = choice.finish_reason or finish
    return ("".join(args) if args else None), "".join(content), finish


def _openai_request(provider: ProviderConfig, kwargs: dict, max_tokens: int):
    """Send kwargs, dropping whatever the endpoint rejects and retrying."""
    from openai import OpenAI

    client = OpenAI(api_key=provider.api_key, base_url=provider.base_url or None, timeout=900, max_retries=1)
    if provider.extra_body:
        kwargs["extra_body"] = dict(provider.extra_body)
    for _ in range(5):
        try:
            return _openai_stream(client, kwargs, provider.model)
        except Exception as e:
            token_key = "max_tokens" if "max_tokens" in kwargs else "max_completion_tokens"
            if "temperature" in kwargs and _mentions(e, "temperature"):
                kwargs.pop("temperature")
            elif kwargs.get(token_key, 0) > FALLBACK_MAX_TOKENS and _mentions(e, "max_tokens", "max_completion_tokens") \
                    and _mentions(e, "range", "exceed", "maximum", "too large", "less than", "at most"):
                kwargs[token_key] = FALLBACK_MAX_TOKENS
            elif "max_tokens" in kwargs and _mentions(e, "max_completion_tokens", "unsupported parameter: 'max_tokens'",
                                                      "max_tokens is not supported"):
                kwargs["max_completion_tokens"] = kwargs.pop("max_tokens")
            elif "max_completion_tokens" in kwargs and _mentions(e, "max_completion_tokens"):
                kwargs["max_tokens"] = kwargs.pop("max_completion_tokens")
            elif isinstance(kwargs.get("tool_choice"), dict) and _mentions(e, "tool_choice", "tool choice"):
                kwargs["tool_choice"] = "required"
            else:
                raise
    raise RuntimeError("OpenAI-compatible request kept being rejected")


def _token_kwargs(provider: ProviderConfig, temperature: float, max_tokens: int) -> dict:
    model = provider.model.lower()
    official = provider.key == "openai" and not provider.base_url
    if official or model.startswith(("o1", "o3", "o4", "gpt-5", "gpt-6", "gpt-7")):
        kw = {"max_completion_tokens": max_tokens}
        if temperature is not None and temperature != 1.0:
            kw["temperature"] = temperature
        return kw
    return {"max_tokens": max_tokens, "temperature": temperature}


def _openai_compatible_tool_call(provider: ProviderConfig, prompt: str, temperature: float, max_tokens: int) -> dict:
    """OpenAI and OpenAI-compatible endpoints (DeepSeek, Qwen, Moonshot, Zhipu, Ollama, relays).

    Official OpenAI models from gpt-5 / o-series on take max_completion_tokens
    and only the default temperature; compatible services usually still want
    max_tokens.  Whatever the endpoint rejects is dropped and the call retried
    (temperature, an oversized token budget, the token parameter name, then
    the forced tool choice).  Responses are streamed.
    """
    kwargs = dict(
        model=provider.model,
        messages=[{"role": "system", "content": TOOL_INSTRUCTION}, {"role": "user", "content": prompt}],
        tools=[{
            "type": "function",
            "function": {
                "name": TOOL_NAME,
                "description": TOOL_DESCRIPTION,
                "parameters": strategy_json_schema(),
            },
        }],
        tool_choice={"type": "function", "function": {"name": TOOL_NAME}},
        **_token_kwargs(provider, temperature, max_tokens),
    )
    args, content, finish = _openai_request(provider, kwargs, max_tokens)
    if args:
        try:
            return json.loads(args)
        except json.JSONDecodeError:
            if finish != "length":
                raise
    if finish == "length":
        raise RuntimeError(f"output hit max tokens={max_tokens} before the tool call finished; raise --max-tokens")
    return _json_from_text(content)


def _plain_json_fallback(provider: ProviderConfig, prompt: str, temperature: float, max_tokens: int) -> dict:
    """Last-resort path for providers/models with no reliable tool-calling
    support: ask for raw JSON in the response body and parse it directly."""
    full_prompt = (
        prompt
        + "\n\nRespond with ONLY a single JSON object matching the schema above. "
        "No prose, no markdown fences, no commentary before or after the JSON."
    )
    kwargs = dict(model=provider.model, messages=[{"role": "user", "content": full_prompt}],
                  **_token_kwargs(provider, temperature, max_tokens))
    _, content, finish = _openai_request(provider, kwargs, max_tokens)
    if finish == "length":
        raise RuntimeError(f"output hit max tokens={max_tokens} before the JSON finished; raise --max-tokens")
    return _json_from_text(content)


_ENVELOPE_KEYS = {"input", "arguments", "parameters", "data", "strategy", "output", "result"}
# Only these field names are ever allowed to be auto-repaired from a
# JSON-encoded string back into real nested structure. Every one of them is
# a list/object field per the schema in registry/schema.py; StringExprS.value,
# Phase.purpose, and other genuine free-text fields are never in this set,
# specifically so a legitimate description that happens to start with `[`
# or `{` (e.g. purpose = "[1, 2]") is never misinterpreted as JSON -- doing
# this by field-name whitelist rather than "any string that looks like
# JSON" is what fixes that false positive.
_STRUCTURAL_FIELD_NAMES = {
    "world", "initial", "derived", "bindings", "args", "items",
    "actors", "focus", "nodes", "transitions", "composition",
}


def _normalize_raw_response(raw, _key=None):
    """Defensive normalization for LLM tool-calling quirks seen in practice
    across providers, applied recursively before Pydantic validation:

    1. The whole payload (or a nested part of it) wrapped in an extra
       single-key envelope like {"input": {...}} instead of the real object
       directly. A genuine StrategyS-shaped dict always has multiple
       required top-level keys (name/world/intent/plan/...), so a
       single-key dict whose one key is a generic wrapper word like "input"
       can never be a legitimate part of the schema -- unwrapping it is
       always safe, never a false positive.
    2. A field that should be nested JSON (list or dict) emitted instead as
       a JSON-encoded STRING, e.g. "bindings": "[...]" rather than
       "bindings": [...]. Only auto-parsed for the whitelisted structural
       field names above -- NOT for arbitrary strings anywhere in the tree,
       since a free-text field can legitimately start with `[` or `{`
       without being JSON at all.

    Runs before every validation attempt, including repair-loop retries, so
    it self-heals if the same quirk recurs.
    """
    if isinstance(raw, str):
        if _key in _STRUCTURAL_FIELD_NAMES:
            s = raw.strip()
            if s[:1] in "[{":
                try:
                    return _normalize_raw_response(json.loads(s))
                except (json.JSONDecodeError, ValueError):
                    return raw
        return raw
    if isinstance(raw, list):
        return [_normalize_raw_response(x) for x in raw]
    if isinstance(raw, dict):
        d = {k: _normalize_raw_response(v, _key=k) for k, v in raw.items()}
        if len(d) == 1:
            ((only_key, only_val),) = d.items()
            if only_key in _ENVELOPE_KEYS and isinstance(only_val, dict):
                return only_val
        return d
    return raw


def _replay_call(provider: ProviderConfig) -> dict:
    """Offline provider: answer #k is the k-th file in provider.base_url
    (os.pathsep-separated .strat or schema .json files; the last one repeats)."""
    import os
    from pathlib import Path
    files = [f for f in provider.base_url.split(os.pathsep) if f]
    index = getattr(provider, "_replay_index", 0)
    setattr(provider, "_replay_index", index + 1)
    path = Path(files[min(index, len(files) - 1)])
    if path.suffix == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    from stratagemdsl.frontend import parse_file
    from stratagemdsl.registry.schema import strategy_to_schema_dict
    return strategy_to_schema_dict(parse_file(path, "lark"))


def call_llm_for_strategy(
    provider: ProviderConfig,
    prompt: str,
    temperature: float = 1.0,
    max_tokens: Optional[int] = None,
    use_tool_calling: bool = True,
) -> tuple[Optional[Strategy], dict, Optional[str]]:
    """
    Returns (strategy_or_None, raw_json_dict, error_message_or_None).
    Dispatches by provider.key; falls back to plain-JSON prompting if
    tool-calling raises (missing SDK feature, provider quirk, etc.).
    max_tokens=None picks the provider default (see DEFAULT_MAX_TOKENS).
    """
    if max_tokens is None:
        max_tokens = default_max_tokens(provider)
    try:
        if provider.key == "replay":
            raw = _replay_call(provider)
        elif provider.key == "anthropic":
            raw = _anthropic_tool_call(provider, prompt, temperature, max_tokens)
        elif use_tool_calling:
            raw = _openai_compatible_tool_call(provider, prompt, temperature, max_tokens)
        else:
            raw = _plain_json_fallback(provider, prompt, temperature, max_tokens)
    except Exception as e:
        if use_tool_calling and provider.key != "anthropic":
            try:
                raw = _plain_json_fallback(provider, prompt, temperature, max_tokens)
            except Exception as e2:
                return None, {}, f"LLM call failed (tool-calling and plain-JSON fallback both failed): {e}; {e2}"
        else:
            return None, {}, f"LLM call failed: {e}"

    raw = _normalize_raw_response(raw)

    try:
        validated = StrategyS.model_validate(raw)
    except Exception as e:
        return None, raw, f"Schema validation failed: {e}"

    try:
        strategy = validated.to_model()
    except Exception as e:
        return None, raw, f"Schema-to-model conversion failed: {e}"

    return strategy, raw, None
