"""A small JSON-answer LLM client for in-game decisions.

`llm.client` asks for one large tool call (a whole strategy); a decision in a
game is a short JSON object every few seconds of game time, so this asks for
plain JSON text and reports token usage. Providers are configured exactly as
for `strat generate` (`llm.config.resolve_provider`).
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Optional, Protocol, Union

from stratagemdsl.llm.client import ProviderConfig


@dataclass
class Reply:
    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    seconds: float = 0.0


class Decider(Protocol):
    model: str

    def ask(self, system: str, user: str) -> Reply: ...


class ProviderDecider:
    """Anthropic through its SDK; every other provider through the OpenAI-compatible SDK."""

    def __init__(self, provider: ProviderConfig, *, max_tokens: int = 4096, temperature: Optional[float] = None):
        self.provider = provider
        self.model = provider.model
        self.max_tokens = max_tokens
        self.temperature = temperature

    def ask(self, system: str, user: str) -> Reply:
        started = time.monotonic()
        if self.provider.key == "anthropic":
            reply = self._anthropic(system, user)
        else:
            reply = self._openai(system, user)
        reply.seconds = round(time.monotonic() - started, 2)
        return reply

    def _anthropic(self, system: str, user: str) -> Reply:
        from anthropic import Anthropic
        p = self.provider
        client = Anthropic(api_key=p.api_key, **({"base_url": p.base_url} if p.base_url else {}))
        kwargs = dict(model=p.model, max_tokens=self.max_tokens, system=system,
                      messages=[{"role": "user", "content": user}])
        if self.temperature is not None:
            kwargs["temperature"] = self.temperature
        try:
            msg = client.messages.create(**kwargs)
        except Exception as e:  # current models reject sampling parameters
            if "temperature" not in kwargs or "temperature" not in str(e).lower():
                raise
            kwargs.pop("temperature")
            msg = client.messages.create(**kwargs)
        text = "".join(getattr(b, "text", "") for b in msg.content if getattr(b, "type", "") == "text")
        usage = getattr(msg, "usage", None)
        return Reply(text, getattr(usage, "input_tokens", 0) or 0, getattr(usage, "output_tokens", 0) or 0)

    def _openai(self, system: str, user: str) -> Reply:
        from openai import OpenAI
        p = self.provider
        client = OpenAI(api_key=p.api_key, base_url=p.base_url or None, timeout=300, max_retries=2)
        kwargs = dict(model=p.model, messages=[{"role": "system", "content": system},
                                               {"role": "user", "content": user}],
                      max_tokens=self.max_tokens)
        if self.temperature is not None:
            kwargs["temperature"] = self.temperature
        if p.extra_body:
            kwargs["extra_body"] = dict(p.extra_body)
        for _ in range(3):
            try:
                resp = client.chat.completions.create(**kwargs)
                break
            except Exception as e:
                msg = str(e).lower()
                if "temperature" in kwargs and "temperature" in msg:
                    kwargs.pop("temperature")
                elif "max_tokens" in kwargs and "max_completion_tokens" in msg:
                    kwargs["max_completion_tokens"] = kwargs.pop("max_tokens")
                else:
                    raise
        else:
            raise RuntimeError("the endpoint kept rejecting the request")
        usage = getattr(resp, "usage", None)
        return Reply(resp.choices[0].message.content or "", getattr(usage, "prompt_tokens", 0) or 0,
                     getattr(usage, "completion_tokens", 0) or 0)


class ScriptedDecider:
    """Answers from a list (or a function of the prompt); for tests and --dry-run without a provider."""

    def __init__(self, answers: Union[list[str], Callable[[str, str], str]], model: str = "scripted"):
        self.answers = answers
        self.model = model
        self.prompts: list[tuple[str, str]] = []

    def ask(self, system: str, user: str) -> Reply:
        self.prompts.append((system, user))
        if callable(self.answers):
            text = self.answers(system, user)
        else:
            text = self.answers[min(len(self.prompts), len(self.answers)) - 1] if self.answers else '{"orders": []}'
        return Reply(text, len(system + user) // 4, len(text) // 4)
