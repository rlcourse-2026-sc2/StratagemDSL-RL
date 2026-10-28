"""Resolve which LLM provider to call, without hard-coding keys.

Precedence (first non-empty wins, per field):
  1. explicit arguments (CLI flags)
  2. STRAT_LLM_PROVIDER / STRAT_LLM_MODEL / STRAT_LLM_API_KEY / STRAT_LLM_BASE_URL
  3. the provider's usual key variable (ANTHROPIC_API_KEY, OPENAI_API_KEY, DEEPSEEK_API_KEY, ...)
  4. a JSON config file: --config, else ~/.stratagemdsl/llm.json, else the smac-ast
     web app's ~/.smac_ast/config.json. Format:
       {"default_provider": "deepseek",
        "providers": {"deepseek": {"apikey": "...", "baseurl": "...", "model": "...",
                                   "extra_body": {"thinking": {"type": "disabled"}}}}}

extra_body (CLI --extra-body, STRAT_LLM_EXTRA_BODY, or the config entry) is merged
into OpenAI-compatible request bodies; --no-thinking adds the provider's switch for
turning reasoning off (THINKING_OFF).

Provider "anthropic" uses the Anthropic SDK; every other name is called through an
OpenAI-compatible endpoint (OpenAI, DeepSeek, Qwen/DashScope, GLM, Moonshot, a
local vLLM/Ollama server, ...). Provider "replay" reads answers from .strat/.json
files instead of calling a model, for offline runs and tests.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from stratagemdsl.llm.client import ProviderConfig

KEY_ENV = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "qwen": "DASHSCOPE_API_KEY",
    "dashscope": "DASHSCOPE_API_KEY",
    "moonshot": "MOONSHOT_API_KEY",
    "zhipu": "ZHIPUAI_API_KEY",
}
DEFAULT_BASE_URL = {
    "deepseek": "https://api.deepseek.com",
    "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "dashscope": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "moonshot": "https://api.moonshot.cn/v1",
    "zhipu": "https://open.bigmodel.cn/api/paas/v4",
    "ollama": "http://localhost:11434/v1",
}
# Request-body switch that turns reasoning off, per provider.  Current Claude
# models always think, so "anthropic" has none.
THINKING_OFF = {
    "deepseek": {"thinking": {"type": "disabled"}},
    "zhipu": {"thinking": {"type": "disabled"}},
    "qwen": {"enable_thinking": False},
    "dashscope": {"enable_thinking": False},
    "openai": {"reasoning_effort": "low"},
}
CONFIG_FILES = (Path.home() / ".stratagemdsl" / "llm.json", Path.home() / ".smac_ast" / "config.json")


def _json_object(text: str, what: str) -> dict:
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{what} is not valid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{what} must be a JSON object")
    return value


def _load_config(path: Optional[Path]) -> dict:
    for candidate in ([path] if path else list(CONFIG_FILES)):
        if candidate and candidate.exists():
            return json.loads(candidate.read_text(encoding="utf-8"))
    return {}


def resolve_provider(provider: Optional[str] = None, model: Optional[str] = None, api_key: Optional[str] = None,
                     base_url: Optional[str] = None, config: Optional[Path] = None,
                     replay: Optional[list[str]] = None, extra_body: Optional[dict] = None,
                     thinking: Optional[bool] = None) -> ProviderConfig:
    if replay:
        return ProviderConfig(key="replay", api_key="-", base_url=os.pathsep.join(map(str, replay)), model="replay")
    cfg = _load_config(Path(config) if config else None)
    key = provider or os.environ.get("STRAT_LLM_PROVIDER") or cfg.get("default_provider") or ""
    if not key:
        raise ValueError("no LLM provider: pass --provider, set STRAT_LLM_PROVIDER, or write ~/.stratagemdsl/llm.json")
    entry = cfg.get("providers", {}).get(key, {})
    resolved = ProviderConfig(
        key=key,
        api_key=api_key or os.environ.get("STRAT_LLM_API_KEY") or os.environ.get(KEY_ENV.get(key, ""), "")
        or entry.get("apikey", ""),
        base_url=base_url or os.environ.get("STRAT_LLM_BASE_URL") or entry.get("baseurl", "")
        or DEFAULT_BASE_URL.get(key, ""),
        model=model or os.environ.get("STRAT_LLM_MODEL") or entry.get("model", ""),
    )
    body = dict(entry.get("extra_body") or {})
    env_body = os.environ.get("STRAT_LLM_EXTRA_BODY")
    if env_body:
        body.update(_json_object(env_body, "STRAT_LLM_EXTRA_BODY"))
    body.update(extra_body or {})
    if thinking is False:
        if key not in THINKING_OFF:
            raise ValueError(f"--no-thinking: no known switch for provider '{key}'"
                             + ("; current Claude models always think" if key == "anthropic" else
                                "; pass the provider's own field with --extra-body"))
        body.update(THINKING_OFF[key])
    resolved.extra_body = body
    if not resolved.model:
        raise ValueError(f"no model for provider '{key}': pass --model or set STRAT_LLM_MODEL")
    if not resolved.api_key and key != "ollama":
        raise ValueError(f"no API key for provider '{key}': pass --api-key or set "
                         f"{KEY_ENV.get(key, 'STRAT_LLM_API_KEY')}")
    resolved.api_key = resolved.api_key or "ollama"
    return resolved
