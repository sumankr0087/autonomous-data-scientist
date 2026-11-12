"""Provider-agnostic LLM client.

A thin abstraction over the LLM provider so agents never import a vendor SDK
directly. Swap providers via `LLM_PROVIDER` in the environment without touching
agent code.

The concrete SDKs (`openai`, `anthropic`) are imported lazily so the package
stays importable even when a provider's SDK isn't installed.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from config.settings import Settings, get_settings

import re

from ads.core.exceptions import ConfigError, LLMError, RateLimitError
from ads.core.logging import get_logger


def _as_rate_limit(msg: str) -> RateLimitError:
    """Parse a provider 429 message into a friendly RateLimitError."""
    low = msg.lower()
    window = None
    if "per day" in low or "perday" in low:
        window = "day"
    elif "per hour" in low or "perhour" in low:
        window = "hour"
    elif "per minute" in low or "perminute" in low:
        window = "minute"

    # Clean, human-friendly retry hint.
    retry_after = None
    secs = None
    m = re.search(r"retryDelay['\"]?:?\s*['\"]?(\d+)s", msg)
    if m:
        secs = int(m.group(1))
    else:
        mm = re.search(r"retry in (?:(\d+)m)?([\d.]+)s", msg)
        if mm:
            secs = int(mm.group(1) or 0) * 60 + int(float(mm.group(2)))
    if secs is not None:
        if secs >= 3600:
            h, m = secs // 3600, (secs % 3600) // 60
            retry_after = f"{h} hr" + (f" {m} min" if m else "")
        elif secs >= 60:
            retry_after = f"{secs // 60} min"
        else:
            retry_after = f"{secs} sec"

    return RateLimitError("LLM usage limit reached", details=msg, retry_after=retry_after, window=window)

log = get_logger(__name__)


@dataclass
class LLMResponse:
    """Normalised response returned by every provider."""

    text: str
    model: str
    raw: Any = None


class BaseLLMClient(ABC):
    """Interface every provider client implements."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @abstractmethod
    def complete(self, prompt: str, *, system: str | None = None, **kwargs: Any) -> LLMResponse:
        """Return a completion for a single prompt."""


class OpenAIClient(BaseLLMClient):
    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)
        if not settings.openai_api_key:
            raise ConfigError("OPENAI_API_KEY is not set but llm_provider=openai")
        try:
            from openai import OpenAI  # lazy import
        except ImportError as exc:  # pragma: no cover
            raise ConfigError("`openai` package not installed. `pip install openai`") from exc
        self._client = OpenAI(api_key=settings.openai_api_key)

    def complete(self, prompt: str, *, system: str | None = None, **kwargs: Any) -> LLMResponse:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        try:
            resp = self._client.chat.completions.create(
                model=self.settings.llm_model,
                messages=messages,
                temperature=kwargs.get("temperature", self.settings.llm_temperature),
                max_tokens=kwargs.get("max_tokens", self.settings.llm_max_tokens),
            )
        except Exception as exc:  # noqa: BLE001
            raise LLMError("OpenAI completion failed", details=str(exc)) from exc
        return LLMResponse(
            text=resp.choices[0].message.content or "",
            model=self.settings.llm_model,
            raw=resp,
        )


class AnthropicClient(BaseLLMClient):
    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)
        if not settings.anthropic_api_key:
            raise ConfigError("ANTHROPIC_API_KEY is not set but llm_provider=anthropic")
        try:
            from anthropic import Anthropic  # lazy import
        except ImportError as exc:  # pragma: no cover
            raise ConfigError("`anthropic` package not installed. `pip install anthropic`") from exc
        self._client = Anthropic(api_key=settings.anthropic_api_key)

    def complete(self, prompt: str, *, system: str | None = None, **kwargs: Any) -> LLMResponse:
        try:
            resp = self._client.messages.create(
                model=self.settings.llm_model,
                system=system or "",
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get("temperature", self.settings.llm_temperature),
                max_tokens=kwargs.get("max_tokens", self.settings.llm_max_tokens),
            )
        except Exception as exc:  # noqa: BLE001
            raise LLMError("Anthropic completion failed", details=str(exc)) from exc
        text = "".join(block.text for block in resp.content if getattr(block, "type", "") == "text")
        return LLMResponse(text=text, model=self.settings.llm_model, raw=resp)


class GeminiClient(BaseLLMClient):
    """Google Gemini via the current `google-genai` SDK (free tier available)."""

    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)
        if not settings.google_api_key:
            raise ConfigError("GOOGLE_API_KEY is not set but llm_provider=gemini")
        try:
            from google import genai  # lazy import
        except ImportError as exc:  # pragma: no cover
            raise ConfigError(
                "`google-genai` not installed. `pip install google-genai`"
            ) from exc
        self._genai = genai
        self._client = genai.Client(api_key=settings.google_api_key)

    def complete(self, prompt: str, *, system: str | None = None, **kwargs: Any) -> LLMResponse:
        from google.genai import types

        # Some models (e.g. gemini-2.5-flash-lite on v1beta) reject a separate
        # system_instruction, so fold it into the prompt for portability.
        contents = f"{system}\n\n{prompt}" if system else prompt
        try:
            resp = self._client.models.generate_content(
                model=self.settings.llm_model,
                contents=contents,
                config=types.GenerateContentConfig(
                    temperature=kwargs.get("temperature", self.settings.llm_temperature),
                    max_output_tokens=kwargs.get("max_tokens", self.settings.llm_max_tokens),
                ),
            )
        except Exception as exc:  # noqa: BLE001
            msg = str(exc)
            if "429" in msg or "RESOURCE_EXHAUSTED" in msg.upper() or "quota" in msg.lower():
                raise _as_rate_limit(msg) from exc
            raise LLMError("Gemini completion failed", details=msg) from exc
        return LLMResponse(text=resp.text or "", model=self.settings.llm_model, raw=resp)


def get_llm_client(settings: Settings | None = None) -> BaseLLMClient:
    """Factory: return the client for the configured provider."""
    settings = settings or get_settings()
    provider = settings.llm_provider
    log.debug("Creating LLM client", extra={"provider": provider, "model": settings.llm_model})
    if provider == "gemini":
        return GeminiClient(settings)
    if provider == "openai":
        return OpenAIClient(settings)
    if provider == "anthropic":
        return AnthropicClient(settings)
    raise ConfigError(f"Unknown llm_provider: {provider}")
