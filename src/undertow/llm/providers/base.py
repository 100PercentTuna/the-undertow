"""
Base LLM provider interface.

All providers MUST implement this interface.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, AsyncGenerator


@dataclass
class LLMResponse:
    """Response from an LLM provider."""

    content: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: int
    finish_reason: str = "stop"
    raw_response: dict[str, Any] = field(default_factory=dict)

    @property
    def total_tokens(self) -> int:
        """Total tokens used."""
        return self.input_tokens + self.output_tokens

    def calculate_cost(
        self,
        input_cost_per_1m: float,
        output_cost_per_1m: float,
    ) -> float:
        """Calculate cost in USD."""
        input_cost = (self.input_tokens / 1_000_000) * input_cost_per_1m
        output_cost = (self.output_tokens / 1_000_000) * output_cost_per_1m
        return input_cost + output_cost


@dataclass
class Message:
    """A message in the conversation."""

    role: str  # "system", "user", "assistant"
    content: str


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    All providers MUST implement:
    - complete(): Single completion
    - stream(): Streaming completion
    - health_check(): Provider availability check
    """

    provider_name: str

    @abstractmethod
    async def complete(
        self,
        messages: list[dict[str, str]],
        model: str,
        *,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stop_sequences: list[str] | None = None,
    ) -> LLMResponse:
        """
        Generate a single completion.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model identifier
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            stop_sequences: Optional stop sequences

        Returns:
            LLMResponse with generated content and metadata
        """
        pass

    @abstractmethod
    async def stream(
        self,
        messages: list[dict[str, str]],
        model: str,
        *,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stop_sequences: list[str] | None = None,
    ) -> AsyncGenerator[str, None]:
        """
        Generate a streaming completion.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model identifier
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            stop_sequences: Optional stop sequences

        Yields:
            Content chunks as they are generated
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the provider is available.

        Returns:
            True if provider is healthy
        """
        pass

    def _get_timestamp(self) -> datetime:
        """Get current UTC timestamp."""
        return datetime.utcnow()

