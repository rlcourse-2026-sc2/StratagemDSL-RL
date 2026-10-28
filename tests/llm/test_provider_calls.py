"""LLM client: request shapes for Claude and OpenAI models, old and current.

Current Claude models reject a forced tool_choice and sampling parameters;
current OpenAI models want max_completion_tokens and the default temperature.
The client starts strict and drops whatever the endpoint refuses.  No network.
"""
import json
import sys
import types
from unittest import mock

import pytest

from stratagemdsl.llm import client as lvc


class _Block:
    def __init__(self, type, **kw):
        self.type = type
        self.__dict__.update(kw)


class _Response:
    def __init__(self, content, stop_reason="tool_use"):
        self.content, self.stop_reason = content, stop_reason


def _fake_anthropic(handler):
    calls = []

    class Stream:
        def __init__(self, response):
            self.response = response

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def __iter__(self):
            return iter([])

        def get_final_message(self):
            return self.response

    class Messages:
        def stream(self, **kwargs):
            calls.append(kwargs)
            return Stream(handler(kwargs))

    class Client:
        def __init__(self, api_key, base_url=None):
            self.base_url = base_url
            self.messages = Messages()
            calls.append({"client_base_url": base_url})

    return types.SimpleNamespace(Anthropic=Client), calls


def _claude(model="claude-opus-5-5", base_url=""):
    return lvc.ProviderConfig(key="anthropic", api_key="x", model=model, base_url=base_url)


def test_current_claude_model_falls_back_to_auto_tool_choice():
    def handler(kw):
        if kw["tool_choice"]["type"] == "tool":
            raise RuntimeError("400 invalid_request_error: tool_choice type 'tool' is not supported for this model")
        return _Response([_Block("thinking", thinking=""), _Block("tool_use", input={"name": "v"})])

    module, calls = _fake_anthropic(handler)
    with mock.patch.dict(sys.modules, {"anthropic": module}):
        raw = lvc._anthropic_tool_call(_claude(), "prompt", temperature=1.0, max_tokens=32000)
    requests = [c for c in calls if "model" in c]
    assert raw == {"name": "v"}
    assert [r["tool_choice"]["type"] for r in requests] == ["tool", "auto"]
    assert all("temperature" not in r for r in requests), "default temperature must not be sent"
    assert "emit_stratagem_variant" in requests[-1]["system"]


def test_claude_text_answer_and_base_url():
    module, calls = _fake_anthropic(lambda kw: _Response(
        [_Block("text", text='Here it is:\n```json\n{"name": "v", "world": []}\n```')], stop_reason="end_turn"))
    with mock.patch.dict(sys.modules, {"anthropic": module}):
        raw = lvc._anthropic_tool_call(_claude(base_url="https://relay.example/anthropic"), "p", 1.0, 100)
    assert raw == {"name": "v", "world": []}
    assert calls[0] == {"client_base_url": "https://relay.example/anthropic"}


def test_claude_truncated_or_refused_answers_say_why():
    module, _ = _fake_anthropic(lambda kw: _Response([_Block("text", text="{")], stop_reason="max_tokens"))
    with mock.patch.dict(sys.modules, {"anthropic": module}), pytest.raises(RuntimeError, match="max-tokens"):
        lvc._anthropic_tool_call(_claude(), "p", 1.0, 100)
    module, _ = _fake_anthropic(lambda kw: _Response([], stop_reason="refusal"))
    with mock.patch.dict(sys.modules, {"anthropic": module}), pytest.raises(RuntimeError, match="refused"):
        lvc._anthropic_tool_call(_claude(), "p", 1.0, 100)


def test_default_output_budget_depends_on_provider():
    assert lvc.default_max_tokens(_claude()) == 32000
    assert lvc.default_max_tokens(lvc.ProviderConfig(key="deepseek")) == 32000
    assert lvc.default_max_tokens(lvc.ProviderConfig(key="qwen")) == 8096


def _ns(**kw):
    return types.SimpleNamespace(**kw)


def _chunks(args, reasoning="", finish="tool_calls"):
    """A streamed tool-call answer, split the way OpenAI-compatible servers send it."""
    out = [_ns(choices=[_ns(delta=_ns(reasoning_content=reasoning[i:i + 5], content=None, tool_calls=None),
                            finish_reason=None)]) for i in range(0, len(reasoning), 5)]
    text = json.dumps(args)
    for i in range(0, len(text), 7):
        call = _ns(index=0, function=_ns(arguments=text[i:i + 7]))
        out.append(_ns(choices=[_ns(delta=_ns(content=None, tool_calls=[call]), finish_reason=None)]))
    out.append(_ns(choices=[_ns(delta=_ns(content=None, tool_calls=None), finish_reason=finish)]))
    return iter(out)


def _fake_openai(handler):
    calls = []

    class Completions:
        def create(self, **kwargs):
            calls.append(kwargs)
            return handler(kwargs)

    class Client:
        def __init__(self, api_key, base_url=None, timeout=None, max_retries=None):
            self.chat = _ns(completions=Completions())

    return _ns(OpenAI=Client), calls


@pytest.mark.parametrize("model", ["gpt-6.1-sol", "gpt-5.5", "o3"])
def test_official_openai_models_use_max_completion_tokens(model):
    module, calls = _fake_openai(lambda kw: _chunks({"name": "v"}))
    with mock.patch.dict(sys.modules, {"openai": module}):
        raw = lvc._openai_compatible_tool_call(lvc.ProviderConfig(key="openai", api_key="x", model=model), "p", 1.0, 9000)
    assert raw == {"name": "v"}
    assert calls[0]["stream"] is True
    assert calls[0]["max_completion_tokens"] == 9000 and "max_tokens" not in calls[0]
    assert "temperature" not in calls[0]


def test_compatible_endpoint_drops_what_it_rejects():
    def handler(kw):
        if "temperature" in kw:
            raise RuntimeError("400 Unsupported value: 'temperature' does not support 0.7")
        if kw["max_tokens"] > 8096:
            raise RuntimeError("400 Invalid max_tokens value, the valid range of max_tokens is [1, 8192]")
        if isinstance(kw["tool_choice"], dict):
            raise RuntimeError("400 tool_choice object is not supported")
        return _chunks({"name": "v"})

    module, calls = _fake_openai(handler)
    provider = lvc.ProviderConfig(key="qwen", api_key="x", model="qwen-max", base_url="https://dashscope")
    with mock.patch.dict(sys.modules, {"openai": module}):
        raw = lvc._openai_compatible_tool_call(provider, "p", 0.7, 32000)
    assert raw == {"name": "v"}
    assert calls[-1]["max_tokens"] == 8096 and calls[-1]["tool_choice"] == "required"
    assert "temperature" not in calls[-1]


def test_deepseek_thinking_stream_reports_progress_and_extra_body(monkeypatch):
    lines = []
    monkeypatch.setattr(lvc, "progress", lines.append)
    monkeypatch.setattr(lvc, "HEARTBEAT_SECONDS", 0.01)

    def handler(kw):
        def slow():
            for chunk in _chunks({"name": "v"}, reasoning="let me think about the ramps " * 4):
                __import__("time").sleep(0.002)
                yield chunk
        return slow()

    module, calls = _fake_openai(handler)
    provider = lvc.ProviderConfig(key="deepseek", api_key="x", model="deepseek-v4-pro",
                                  base_url="https://api.deepseek.com", extra_body={"thinking": {"type": "disabled"}})
    with mock.patch.dict(sys.modules, {"openai": module}):
        raw = lvc._openai_compatible_tool_call(provider, "p", 1.0, 32000)
    assert raw == {"name": "v"}
    assert calls[0]["extra_body"] == {"thinking": {"type": "disabled"}}
    assert lines and "deepseek-v4-pro" in lines[0] and "reasoning" in lines[0]


def test_truncated_stream_says_raise_max_tokens():
    module, _ = _fake_openai(lambda kw: iter([_ns(choices=[_ns(
        delta=_ns(content=None, tool_calls=[_ns(index=0, function=_ns(arguments='{"name": "v", "wor'))]),
        finish_reason="length")])]))
    provider = lvc.ProviderConfig(key="deepseek", api_key="x", model="deepseek-v4-pro")
    with mock.patch.dict(sys.modules, {"openai": module}), pytest.raises(RuntimeError, match="max-tokens"):
        lvc._openai_compatible_tool_call(provider, "p", 1.0, 32000)


def test_no_thinking_and_extra_body_resolution(monkeypatch, tmp_path):
    from stratagemdsl.llm.config import resolve_provider
    for var in ("STRAT_LLM_PROVIDER", "STRAT_LLM_MODEL", "STRAT_LLM_API_KEY", "STRAT_LLM_BASE_URL", "STRAT_LLM_EXTRA_BODY"):
        monkeypatch.delenv(var, raising=False)
    cfg = tmp_path / "llm.json"
    cfg.write_text(json.dumps({"providers": {"deepseek": {"apikey": "k", "model": "deepseek-v4-pro",
                                                          "extra_body": {"top_p": 0.9}}}}), encoding="utf-8")
    p = resolve_provider("deepseek", config=cfg, thinking=False)
    assert p.extra_body == {"top_p": 0.9, "thinking": {"type": "disabled"}}
    monkeypatch.setenv("STRAT_LLM_EXTRA_BODY", '{"enable_thinking": false}')
    assert resolve_provider("qwen", model="qwen-max", api_key="k", config=cfg).extra_body == {"enable_thinking": False}
    with pytest.raises(ValueError, match="always think"):
        resolve_provider("anthropic", model="claude-sonnet-5-5", api_key="k", config=cfg, thinking=False)
