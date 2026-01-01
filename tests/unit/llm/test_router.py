"""
Tests for Model Router.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from undertow.llm.router import ModelRouter, CostTracker, ResponseCache
from undertow.llm.providers.base import LLMResponse
from undertow.llm.tiers import ModelTier
from undertow.exceptions import BudgetExceededError


class TestCostTracker:
    """Tests for CostTracker."""

    def test_tracks_daily_spend(self):
        """Test daily spend tracking."""
        tracker = CostTracker(daily_limit=100.0)
        
        tracker.record(
            task_name="test",
            provider="mock",
            model="test-model",
            input_tokens=1000,
            output_tokens=500,
            cost_usd=0.05,
        )
        
        assert tracker.daily_spend == 0.05
        assert tracker.remaining_budget == 99.95

    def test_can_spend_check(self):
        """Test budget check."""
        tracker = CostTracker(daily_limit=1.0)
        
        assert tracker.can_spend(0.5)
        assert tracker.can_spend(1.0)
        assert not tracker.can_spend(1.1)

    def test_multiple_records(self):
        """Test multiple cost records."""
        tracker = CostTracker(daily_limit=100.0)
        
        for i in range(5):
            tracker.record(
                task_name=f"test_{i}",
                provider="mock",
                model="test-model",
                input_tokens=1000,
                output_tokens=500,
                cost_usd=1.0,
            )
        
        assert tracker.daily_spend == 5.0
        assert len(tracker.records) == 5


class TestResponseCache:
    """Tests for ResponseCache."""

    def test_cache_set_and_get(self):
        """Test cache set and retrieval."""
        cache = ResponseCache(max_size=100)
        
        response = LLMResponse(
            content="test content",
            model="test-model",
            input_tokens=100,
            output_tokens=50,
            latency_ms=500,
        )
        
        messages = [{"role": "user", "content": "test"}]
        
        cache.set(messages, "test-model", 0.1, response)
        cached = cache.get(messages, "test-model", 0.1)
        
        assert cached is not None
        assert cached.content == "test content"

    def test_cache_miss(self):
        """Test cache miss."""
        cache = ResponseCache(max_size=100)
        
        messages = [{"role": "user", "content": "test"}]
        cached = cache.get(messages, "test-model", 0.1)
        
        assert cached is None

    def test_cache_eviction(self):
        """Test cache eviction at max size."""
        cache = ResponseCache(max_size=2)
        
        response = LLMResponse(
            content="test",
            model="test",
            input_tokens=10,
            output_tokens=5,
            latency_ms=100,
        )
        
        # Add 3 items to cache with max_size=2
        cache.set([{"role": "user", "content": "1"}], "m", 0.1, response)
        cache.set([{"role": "user", "content": "2"}], "m", 0.1, response)
        cache.set([{"role": "user", "content": "3"}], "m", 0.1, response)
        
        # Should have evicted oldest
        assert len(cache._cache) == 2


class TestModelRouter:
    """Tests for ModelRouter."""

    @pytest.fixture
    def mock_provider(self):
        """Create mock provider."""
        provider = MagicMock()
        provider.complete = AsyncMock(return_value=LLMResponse(
            content="test response",
            model="test-model",
            input_tokens=100,
            output_tokens=50,
            latency_ms=500,
        ))
        return provider

    @pytest.fixture
    def router(self, mock_provider):
        """Create router with mock provider."""
        return ModelRouter(
            providers={"mock": mock_provider},
            preference="mock",
            daily_budget=100.0,
        )

    @pytest.mark.asyncio
    async def test_complete_basic(self, router, mock_provider):
        """Test basic completion."""
        response = await router.complete(
            task_name="test_task",
            messages=[{"role": "user", "content": "hello"}],
        )
        
        assert response.content == "test response"
        mock_provider.complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_budget_exceeded(self, mock_provider):
        """Test budget exceeded error."""
        router = ModelRouter(
            providers={"mock": mock_provider},
            preference="mock",
            daily_budget=0.0001,  # Very low budget
        )
        
        # Add existing spend
        router.cost_tracker.record(
            task_name="previous",
            provider="mock",
            model="test",
            input_tokens=1000000,
            output_tokens=1000000,
            cost_usd=100.0,
        )
        
        with pytest.raises(BudgetExceededError):
            await router.complete(
                task_name="test",
                messages=[{"role": "user", "content": "hello"}],
            )

    @pytest.mark.asyncio
    async def test_cost_tracking(self, router, mock_provider):
        """Test cost tracking after completion."""
        await router.complete(
            task_name="test_task",
            messages=[{"role": "user", "content": "hello"}],
        )
        
        assert router.cost_tracker.daily_spend > 0
        assert len(router.cost_tracker.records) == 1
        assert router.cost_tracker.records[0].task_name == "test_task"

    @pytest.mark.asyncio
    async def test_caching(self, router, mock_provider):
        """Test response caching."""
        messages = [{"role": "user", "content": "hello"}]
        
        # First call
        await router.complete(
            task_name="test",
            messages=messages,
            temperature=0.0,  # Low temp enables caching
        )
        
        # Second call should hit cache
        await router.complete(
            task_name="test",
            messages=messages,
            temperature=0.0,
        )
        
        # Provider should only be called once
        assert mock_provider.complete.call_count == 1

