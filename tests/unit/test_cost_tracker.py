"""
Unit tests for Cost Tracker service.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from undertow.services.cost_tracker import CostTracker, CostEntry, DailyCostSummary


@pytest.fixture
def mock_cache() -> MagicMock:
    """Create mock cache."""
    cache = MagicMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    return cache


@pytest.fixture
def tracker(mock_cache: MagicMock) -> CostTracker:
    """Create cost tracker with mock cache."""
    tracker = CostTracker(daily_budget_usd=100.0)
    tracker._cache = mock_cache
    return tracker


class TestCostEntry:
    """Tests for CostEntry dataclass."""

    def test_cost_entry_creation(self) -> None:
        """Test CostEntry creation."""
        entry = CostEntry(
            agent_name="motivation",
            model="claude-sonnet-4-20250514",
            input_tokens=1000,
            output_tokens=500,
            cost_usd=0.05,
        )

        assert entry.agent_name == "motivation"
        assert entry.cost_usd == 0.05
        assert entry.story_id is None

    def test_cost_entry_with_story_id(self) -> None:
        """Test CostEntry with optional fields."""
        entry = CostEntry(
            agent_name="chains",
            model="claude-sonnet-4-20250514",
            input_tokens=2000,
            output_tokens=1000,
            cost_usd=0.10,
            story_id="story-123",
            pipeline_run_id="run-456",
        )

        assert entry.story_id == "story-123"
        assert entry.pipeline_run_id == "run-456"


class TestCostTracker:
    """Tests for CostTracker service."""

    @pytest.mark.asyncio
    async def test_record_cost(
        self,
        tracker: CostTracker,
        mock_cache: MagicMock,
    ) -> None:
        """Test recording a cost entry."""
        await tracker.record(
            agent_name="motivation",
            model="claude-sonnet-4-20250514",
            input_tokens=1000,
            output_tokens=500,
            cost_usd=0.05,
        )

        # Entry should be stored in memory
        assert len(tracker._entries) == 1
        assert tracker._entries[0].agent_name == "motivation"

        # Cache should be updated
        mock_cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_daily_summary_empty(
        self,
        tracker: CostTracker,
        mock_cache: MagicMock,
    ) -> None:
        """Test getting daily summary with no data."""
        summary = await tracker.get_daily_summary()

        assert summary.total_cost_usd == 0
        assert summary.total_calls == 0
        assert summary.budget_usd == 100.0
        assert summary.budget_remaining_usd == 100.0

    @pytest.mark.asyncio
    async def test_get_daily_summary_with_data(
        self,
        tracker: CostTracker,
        mock_cache: MagicMock,
    ) -> None:
        """Test getting daily summary with cached data."""
        import json

        mock_cache.get = AsyncMock(return_value=json.dumps({
            "total_cost_usd": 25.50,
            "total_calls": 100,
            "total_input_tokens": 500000,
            "total_output_tokens": 250000,
            "by_agent": {"motivation": 10.0, "chains": 15.5},
            "by_model": {"claude-sonnet-4-20250514": 25.50},
        }))

        summary = await tracker.get_daily_summary()

        assert summary.total_cost_usd == 25.50
        assert summary.total_calls == 100
        assert summary.budget_remaining_usd == 74.50
        assert summary.budget_used_pct == 25.50

    @pytest.mark.asyncio
    async def test_is_over_budget_false(
        self,
        tracker: CostTracker,
        mock_cache: MagicMock,
    ) -> None:
        """Test budget check when under budget."""
        import json

        mock_cache.get = AsyncMock(return_value=json.dumps({
            "total_cost_usd": 50.0,
            "total_calls": 200,
            "total_input_tokens": 1000000,
            "total_output_tokens": 500000,
            "by_agent": {},
            "by_model": {},
        }))

        is_over = await tracker.is_over_budget()
        assert is_over is False

    @pytest.mark.asyncio
    async def test_is_over_budget_true(
        self,
        tracker: CostTracker,
        mock_cache: MagicMock,
    ) -> None:
        """Test budget check when over budget."""
        import json

        mock_cache.get = AsyncMock(return_value=json.dumps({
            "total_cost_usd": 150.0,  # Over the $100 budget
            "total_calls": 500,
            "total_input_tokens": 3000000,
            "total_output_tokens": 1500000,
            "by_agent": {},
            "by_model": {},
        }))

        is_over = await tracker.is_over_budget()
        assert is_over is True

    def test_get_session_costs(self, tracker: CostTracker) -> None:
        """Test getting session costs."""
        # Add some entries directly
        tracker._entries = [
            CostEntry("agent1", "model1", 100, 50, 0.01),
            CostEntry("agent1", "model1", 100, 50, 0.02),
            CostEntry("agent2", "model2", 200, 100, 0.03),
        ]

        costs = tracker.get_session_costs()

        assert costs["session_total_usd"] == 0.06
        assert costs["session_calls"] == 3
        assert costs["by_agent"]["agent1"] == 0.03
        assert costs["by_agent"]["agent2"] == 0.03
        assert costs["by_model"]["model1"] == 0.03
        assert costs["by_model"]["model2"] == 0.03


class TestDailyCostSummary:
    """Tests for DailyCostSummary dataclass."""

    def test_summary_creation(self) -> None:
        """Test DailyCostSummary creation."""
        summary = DailyCostSummary(
            date="2025-01-01",
            total_cost_usd=50.0,
            total_calls=200,
            total_input_tokens=1000000,
            total_output_tokens=500000,
            by_agent={"motivation": 25.0, "chains": 25.0},
            by_model={"claude-sonnet-4-20250514": 50.0},
            budget_usd=100.0,
            budget_remaining_usd=50.0,
            budget_used_pct=50.0,
        )

        assert summary.date == "2025-01-01"
        assert summary.total_cost_usd == 50.0
        assert summary.budget_used_pct == 50.0

