"""
Anthropic Claude provider implementation.
"""

import time
from typing import AsyncGenerator

import anthropic
import structlog

from undertow.exceptions import (
    ContextLengthError,
    InvalidResponseError,
    ProviderUnavailableError,
    RateLimitError,
)
from undertow.llm.providers.base import BaseLLMProvider, LLMResponse

logger = structlog.get_logger()


class AnthropicProvider(BaseLLMProvider):
    """
    Anthropic Claude API provider.

    Supports Claude 3.5 and Claude 4 model families.
    """

    provider_name = "anthropic"

    def __init__(self, api_key: str) -> None:
        """
        Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key
        """
        self.client = anthropic.AsyncAnthropic(api_key=api_key)

    async def complete(
        self,
        messages: list[dict[str, str]],
        model: str,
        *,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stop_sequences: list[str] | None = None,
    ) -> LLMResponse:
        """Generate completion using Anthropic API."""
        start_time = time.perf_counter()

        # Extract system message if present
        system_message = None
        user_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                user_messages.append(msg)

        try:
            kwargs: dict = {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": user_messages,
            }

            if system_message:
                kwargs["system"] = system_message

            if stop_sequences:
                kwargs["stop_sequences"] = stop_sequences

            response = await self.client.messages.create(**kwargs)

            latency_ms = int((time.perf_counter() - start_time) * 1000)

            # Extract content from response
            content = ""
            if response.content:
                content = response.content[0].text

            return LLMResponse(
                content=content,
                model=model,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                latency_ms=latency_ms,
                finish_reason=response.stop_reason or "stop",
                raw_response=response.model_dump(),
            )

        except anthropic.RateLimitError as e:
            logger.warning("Anthropic rate limit exceeded", error=str(e))
            raise RateLimitError(
                provider="anthropic",
                retry_after=60.0,  # Default retry after
            ) from e

        except anthropic.BadRequestError as e:
            if "context_length" in str(e).lower():
                raise ContextLengthError(
                    max_tokens=200000,  # Claude's context window
                    actual_tokens=0,  # Unknown
                ) from e
            raise InvalidResponseError(f"Bad request: {e}") from e

        except anthropic.APIStatusError as e:
            logger.error("Anthropic API error", error=str(e), status=e.status_code)
            raise ProviderUnavailableError(f"Anthropic API error: {e}") from e

        except Exception as e:
            logger.error("Unexpected Anthropic error", error=str(e))
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
        """Generate streaming completion using Anthropic API."""
        # Extract system message if present
        system_message = None
        user_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                user_messages.append(msg)

        try:
            kwargs: dict = {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": user_messages,
            }

            if system_message:
                kwargs["system"] = system_message

            if stop_sequences:
                kwargs["stop_sequences"] = stop_sequences

            async with self.client.messages.stream(**kwargs) as stream:
                async for text in stream.text_stream:
                    yield text

        except anthropic.RateLimitError as e:
            logger.warning("Anthropic rate limit exceeded during stream", error=str(e))
            raise RateLimitError(provider="anthropic", retry_after=60.0) from e

        except Exception as e:
            logger.error("Anthropic streaming error", error=str(e))
            raise ProviderUnavailableError(f"Streaming error: {e}") from e

    async def health_check(self) -> bool:
        """Check if Anthropic API is available."""
        try:
            # Simple test call
            response = await self.client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}],
            )
            return bool(response.content)
        except Exception as e:
            logger.warning("Anthropic health check failed", error=str(e))
            return False

