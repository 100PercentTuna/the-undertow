"""
OpenAI provider implementation.
"""

import time
from typing import AsyncGenerator

import openai
import structlog

from undertow.exceptions import (
    ContextLengthError,
    InvalidResponseError,
    ProviderUnavailableError,
    RateLimitError,
)
from undertow.llm.providers.base import BaseLLMProvider, LLMResponse

logger = structlog.get_logger()


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI API provider.

    Supports GPT-4o and GPT-4o-mini models.
    """

    provider_name = "openai"

    def __init__(self, api_key: str) -> None:
        """
        Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key
        """
        self.client = openai.AsyncOpenAI(api_key=api_key)

    async def complete(
        self,
        messages: list[dict[str, str]],
        model: str,
        *,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stop_sequences: list[str] | None = None,
    ) -> LLMResponse:
        """Generate completion using OpenAI API."""
        start_time = time.perf_counter()

        try:
            kwargs: dict = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }

            if stop_sequences:
                kwargs["stop"] = stop_sequences

            response = await self.client.chat.completions.create(**kwargs)

            latency_ms = int((time.perf_counter() - start_time) * 1000)

            # Extract content from response
            content = ""
            if response.choices and response.choices[0].message.content:
                content = response.choices[0].message.content

            finish_reason = "stop"
            if response.choices and response.choices[0].finish_reason:
                finish_reason = response.choices[0].finish_reason

            return LLMResponse(
                content=content,
                model=model,
                input_tokens=response.usage.prompt_tokens if response.usage else 0,
                output_tokens=response.usage.completion_tokens if response.usage else 0,
                latency_ms=latency_ms,
                finish_reason=finish_reason,
                raw_response=response.model_dump(),
            )

        except openai.RateLimitError as e:
            logger.warning("OpenAI rate limit exceeded", error=str(e))
            raise RateLimitError(
                provider="openai",
                retry_after=60.0,
            ) from e

        except openai.BadRequestError as e:
            if "context_length" in str(e).lower() or "maximum context" in str(e).lower():
                raise ContextLengthError(
                    max_tokens=128000,  # GPT-4o context window
                    actual_tokens=0,
                ) from e
            raise InvalidResponseError(f"Bad request: {e}") from e

        except openai.APIStatusError as e:
            logger.error("OpenAI API error", error=str(e), status=e.status_code)
            raise ProviderUnavailableError(f"OpenAI API error: {e}") from e

        except Exception as e:
            logger.error("Unexpected OpenAI error", error=str(e))
            raise ProviderUnavailableError(f"Unexpected error: {e}") from e

    async def stream(
        self,
        messages: list[dict[str, str]],
        model: str,
        *,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stop_sequences: list[str] | None = None,
    ) -> AsyncGenerator[str, None]:
        """Generate streaming completion using OpenAI API."""
        try:
            kwargs: dict = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": True,
            }

            if stop_sequences:
                kwargs["stop"] = stop_sequences

            stream = await self.client.chat.completions.create(**kwargs)

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except openai.RateLimitError as e:
            logger.warning("OpenAI rate limit exceeded during stream", error=str(e))
            raise RateLimitError(provider="openai", retry_after=60.0) from e

        except Exception as e:
            logger.error("OpenAI streaming error", error=str(e))
            raise ProviderUnavailableError(f"Streaming error: {e}") from e

    async def health_check(self) -> bool:
        """Check if OpenAI API is available."""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}],
            )
            return bool(response.choices)
        except Exception as e:
            logger.warning("OpenAI health check failed", error=str(e))
            return False

