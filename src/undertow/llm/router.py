"""
Intelligent model router for The Undertow.

Routes requests to appropriate models based on:
- Task type and complexity
- User provider preference
- Cost constraints
- Caching opportunities
"""

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import structlog
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from undertow.config import settings
from undertow.exceptions import (
    BudgetExceededError,
    LLMError,
    ProviderUnavailableError,
    RateLimitError,
)
from undertow.llm.providers.base import BaseLLMProvider, LLMResponse
from undertow.llm.tiers import (
    MODELS,
    ModelConfig,
    ModelTier,
    get_preferred_provider,
    get_tier_for_task,
)

logger = structlog.get_logger()


@dataclass
class RoutingDecision:
    """Decision about which model to use."""

    provider: str
    model: str
    tier: ModelTier
    model_config: ModelConfig
    from_cache: bool = False


@dataclass
class CostRecord:
    """Record of a model invocation cost."""

    timestamp: datetime
    task_name: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float


class CostTracker:
    """Tracks daily spend across all model calls."""

    def __init__(self, daily_limit: float = 50.0) -> None:
        self.daily_limit = daily_limit
        self.records: list[CostRecord] = []
        self._today: str = ""

    def _check_reset(self) -> None:
        """Reset if new day."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        if today != self._today:
            self.records = []
            self._today = today

    @property
    def daily_spend(self) -> float:
        """Get total spend today."""
        self._check_reset()
        return sum(r.cost_usd for r in self.records)

    @property
    def remaining_budget(self) -> float:
        """Get remaining budget for today."""
        return max(0, self.daily_limit - self.daily_spend)

    def can_spend(self, estimated_cost: float) -> bool:
        """Check if we can afford this spend."""
        return self.remaining_budget >= estimated_cost

    def record(
        self,
        task_name: str,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
    ) -> None:
        """Record a cost."""
        self._check_reset()
        self.records.append(
            CostRecord(
                timestamp=datetime.utcnow(),
                task_name=task_name,
                provider=provider,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost_usd,
            )
        )
        logger.info(
            "Cost recorded",
            task=task_name,
            cost=cost_usd,
            daily_total=self.daily_spend,
        )


class ResponseCache:
    """Simple in-memory cache for LLM responses."""

    def __init__(self, max_size: int = 1000) -> None:
        self.max_size = max_size
        self._cache: dict[str, tuple[LLMResponse, datetime]] = {}

    def _make_key(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float,
    ) -> str:
        """Create cache key from request parameters."""
        content = json.dumps(
            {
                "messages": messages,
                "model": model,
                "temperature": temperature,
            },
            sort_keys=True,
        )
        return hashlib.sha256(content.encode()).hexdigest()

    def get(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float,
    ) -> LLMResponse | None:
        """Get cached response if exists and not expired."""
        key = self._make_key(messages, model, temperature)
        if key in self._cache:
            response, cached_at = self._cache[key]
            # Cache valid for 1 hour
            if (datetime.utcnow() - cached_at).total_seconds() < 3600:
                return response
            else:
                del self._cache[key]
        return None

    def set(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float,
        response: LLMResponse,
    ) -> None:
        """Cache a response."""
        # Evict oldest if at capacity
        if len(self._cache) >= self.max_size:
            oldest_key = min(self._cache, key=lambda k: self._cache[k][1])
            del self._cache[oldest_key]

        key = self._make_key(messages, model, temperature)
        self._cache[key] = (response, datetime.utcnow())


class ModelRouter:
    """
    Intelligent model routing with fallback and cost management.

    Features:
    - Routes requests based on task type
    - Handles provider failover
    - Tracks and limits costs
    - Caches responses
    - Retries with exponential backoff
    """

    def __init__(
        self,
        providers: dict[str, BaseLLMProvider],
        preference: str = "anthropic",
        daily_budget: float | None = None,
    ) -> None:
        """
        Initialize router.

        Args:
            providers: Dict mapping provider names to provider instances
            preference: Default provider preference
            daily_budget: Daily budget limit in USD
        """
        self.providers = providers
        self.preference = preference
        self.cost_tracker = CostTracker(
            daily_limit=daily_budget or settings.ai_daily_budget_usd
        )
        self.cache = ResponseCache()

        # Track last request metadata
        self.last_model_used: str = ""
        self.last_input_tokens: int = 0
        self.last_output_tokens: int = 0
        self.last_cost: float = 0.0

    async def complete(
        self,
        task_name: str,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        force_tier: ModelTier | None = None,
        force_provider: str | None = None,
        use_cache: bool = True,
    ) -> LLMResponse:
        """
        Route and execute LLM request.

        Args:
            task_name: Name of the task for routing
            messages: Conversation messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            force_tier: Override automatic tier selection
            force_provider: Override provider selection
            use_cache: Whether to use/check cache

        Returns:
            LLMResponse with generated content
        """
        # Determine routing
        routing = self._route(task_name, force_tier, force_provider)

        # Check cache
        if use_cache and temperature < 0.3:  # Only cache low-temperature
            cached = self.cache.get(messages, routing.model, temperature)
            if cached:
                logger.debug("Cache hit", task=task_name)
                self._update_last_request_metadata(cached, routing, cost=0.0)
                return cached

        # Check budget
        estimated_cost = self._estimate_cost(messages, max_tokens, routing.model_config)
        if not self.cost_tracker.can_spend(estimated_cost):
            raise BudgetExceededError(
                daily_limit=self.cost_tracker.daily_limit,
                current_spend=self.cost_tracker.daily_spend,
            )

        # Execute with retries
        response = await self._execute_with_retries(
            routing=routing,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Calculate actual cost
        cost = response.calculate_cost(
            routing.model_config.input_cost_per_1m,
            routing.model_config.output_cost_per_1m,
        )

        # Track cost
        self.cost_tracker.record(
            task_name=task_name,
            provider=routing.provider,
            model=routing.model,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            cost_usd=cost,
        )

        # Update metadata
        self._update_last_request_metadata(response, routing, cost)

        # Cache if appropriate
        if use_cache and temperature < 0.3:
            self.cache.set(messages, routing.model, temperature, response)

        return response

    def _route(
        self,
        task_name: str,
        force_tier: ModelTier | None,
        force_provider: str | None,
    ) -> RoutingDecision:
        """Determine which model to use."""
        # Determine tier
        tier = force_tier or get_tier_for_task(task_name)

        # Determine provider
        if force_provider and force_provider in self.providers:
            provider = force_provider
        elif self.preference == "best_fit":
            provider = get_preferred_provider(task_name, "anthropic")
        else:
            provider = self.preference

        # Ensure provider is available
        if provider not in self.providers:
            # Fall back to first available
            provider = next(iter(self.providers.keys()))

        # Get model config
        model_config = MODELS[provider][tier]

        return RoutingDecision(
            provider=provider,
            model=model_config.model_id,
            tier=tier,
            model_config=model_config,
        )

    async def _execute_with_retries(
        self,
        routing: RoutingDecision,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> LLMResponse:
        """Execute request with retries and fallback."""
        provider_order = self._get_provider_order(routing.provider)

        last_error: Exception | None = None

        for provider_name in provider_order:
            provider = self.providers.get(provider_name)
            if not provider:
                continue

            model_config = MODELS[provider_name][routing.tier]

            try:
                async for attempt in AsyncRetrying(
                    stop=stop_after_attempt(3),
                    wait=wait_exponential(multiplier=1, min=2, max=30),
                    retry=retry_if_exception_type(RateLimitError),
                    reraise=True,
                ):
                    with attempt:
                        response = await provider.complete(
                            messages=messages,
                            model=model_config.model_id,
                            temperature=temperature,
                            max_tokens=max_tokens,
                        )
                        return response

            except RateLimitError as e:
                logger.warning(
                    "Rate limit after retries, trying fallback",
                    provider=provider_name,
                )
                last_error = e
                continue

            except ProviderUnavailableError as e:
                logger.warning(
                    "Provider unavailable, trying fallback",
                    provider=provider_name,
                    error=str(e),
                )
                last_error = e
                continue

            except LLMError as e:
                logger.error(
                    "LLM error, trying fallback",
                    provider=provider_name,
                    error=str(e),
                )
                last_error = e
                continue

        # All providers failed
        raise ProviderUnavailableError(
            f"All providers failed. Last error: {last_error}"
        )

    def _get_provider_order(self, primary: str) -> list[str]:
        """Get provider order for failover."""
        order = [primary]
        for provider in self.providers:
            if provider not in order:
                order.append(provider)
        return order

    def _estimate_cost(
        self,
        messages: list[dict[str, str]],
        max_tokens: int,
        config: ModelConfig,
    ) -> float:
        """Estimate cost for a request."""
        # Rough token estimate: 4 chars per token
        input_chars = sum(len(m["content"]) for m in messages)
        estimated_input = input_chars // 4

        # Assume half of max_tokens for output
        estimated_output = max_tokens // 2

        input_cost = (estimated_input / 1_000_000) * config.input_cost_per_1m
        output_cost = (estimated_output / 1_000_000) * config.output_cost_per_1m

        return input_cost + output_cost

    def _update_last_request_metadata(
        self,
        response: LLMResponse,
        routing: RoutingDecision,
        cost: float,
    ) -> None:
        """Update metadata from last request."""
        self.last_model_used = response.model
        self.last_input_tokens = response.input_tokens
        self.last_output_tokens = response.output_tokens
        self.last_cost = cost

