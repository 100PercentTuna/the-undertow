"""
Cost tracking service.

Tracks AI spending across the system with budget enforcement.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

import structlog

from undertow.config import settings
from undertow.infrastructure.cache import get_cache

logger = structlog.get_logger()


@dataclass
class CostEntry:
    """A single cost entry."""

    agent_name: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    story_id: str | None = None
    pipeline_run_id: str | None = None


@dataclass
class DailyCostSummary:
    """Summary of daily costs."""

    date: str
    total_cost_usd: float
    total_calls: int
    total_input_tokens: int
    total_output_tokens: int
    by_agent: dict[str, float] = field(default_factory=dict)
    by_model: dict[str, float] = field(default_factory=dict)
    budget_usd: float = 0.0
    budget_remaining_usd: float = 0.0
    budget_used_pct: float = 0.0


class CostTracker:
    """
    Service for tracking AI costs.

    Maintains daily totals, enforces budgets, and provides analytics.

    Example:
        tracker = CostTracker()

        # Record a cost
        await tracker.record(
            agent_name="motivation",
            model="claude-sonnet-4-20250514",
            input_tokens=1000,
            output_tokens=500,
            cost_usd=0.05,
        )

        # Check budget
        if await tracker.is_over_budget():
            raise BudgetExceededError()

        # Get summary
        summary = await tracker.get_daily_summary()
    """

    CACHE_KEY_PREFIX = "cost:"
    CACHE_TTL = 86400 * 7  # 7 days

    def __init__(self, daily_budget_usd: float | None = None) -> None:
        """
        Initialize cost tracker.

        Args:
            daily_budget_usd: Daily budget limit (defaults to settings)
        """
        self.daily_budget_usd = daily_budget_usd or settings.ai_daily_budget_usd
        self._cache = get_cache()
        self._entries: list[CostEntry] = []
        self._lock = asyncio.Lock()

    async def record(
        self,
        agent_name: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        story_id: str | None = None,
        pipeline_run_id: str | None = None,
    ) -> None:
        """
        Record a cost entry.

        Args:
            agent_name: Name of the agent
            model: Model used
            input_tokens: Input token count
            output_tokens: Output token count
            cost_usd: Cost in USD
            story_id: Optional story ID
            pipeline_run_id: Optional pipeline run ID
        """
        entry = CostEntry(
            agent_name=agent_name,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            story_id=story_id,
            pipeline_run_id=pipeline_run_id,
        )

        async with self._lock:
            self._entries.append(entry)

            # Update daily total in cache
            today = datetime.utcnow().strftime("%Y-%m-%d")
            cache_key = f"{self.CACHE_KEY_PREFIX}daily:{today}"

            try:
                current = await self._cache.get(cache_key)
                if current:
                    import json
                    data = json.loads(current)
                    data["total_cost_usd"] += cost_usd
                    data["total_calls"] += 1
                    data["total_input_tokens"] += input_tokens
                    data["total_output_tokens"] += output_tokens
                    data["by_agent"][agent_name] = data["by_agent"].get(agent_name, 0) + cost_usd
                    data["by_model"][model] = data["by_model"].get(model, 0) + cost_usd
                else:
                    data = {
                        "total_cost_usd": cost_usd,
                        "total_calls": 1,
                        "total_input_tokens": input_tokens,
                        "total_output_tokens": output_tokens,
                        "by_agent": {agent_name: cost_usd},
                        "by_model": {model: cost_usd},
                    }

                import json
                await self._cache.set(cache_key, json.dumps(data), ttl=self.CACHE_TTL)

            except Exception as e:
                logger.warning("Failed to update cost cache", error=str(e))

        logger.debug(
            "Cost recorded",
            agent=agent_name,
            model=model,
            cost_usd=cost_usd,
        )

    async def get_daily_summary(self, date: str | None = None) -> DailyCostSummary:
        """
        Get cost summary for a day.

        Args:
            date: Date string (YYYY-MM-DD), defaults to today

        Returns:
            DailyCostSummary
        """
        date = date or datetime.utcnow().strftime("%Y-%m-%d")
        cache_key = f"{self.CACHE_KEY_PREFIX}daily:{date}"

        try:
            data = await self._cache.get(cache_key)
            if data:
                import json
                parsed = json.loads(data)
            else:
                parsed = {
                    "total_cost_usd": 0,
                    "total_calls": 0,
                    "total_input_tokens": 0,
                    "total_output_tokens": 0,
                    "by_agent": {},
                    "by_model": {},
                }
        except Exception:
            parsed = {
                "total_cost_usd": 0,
                "total_calls": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "by_agent": {},
                "by_model": {},
            }

        total_cost = parsed["total_cost_usd"]
        remaining = max(0, self.daily_budget_usd - total_cost)
        used_pct = (total_cost / self.daily_budget_usd * 100) if self.daily_budget_usd > 0 else 0

        return DailyCostSummary(
            date=date,
            total_cost_usd=total_cost,
            total_calls=parsed["total_calls"],
            total_input_tokens=parsed["total_input_tokens"],
            total_output_tokens=parsed["total_output_tokens"],
            by_agent=parsed["by_agent"],
            by_model=parsed["by_model"],
            budget_usd=self.daily_budget_usd,
            budget_remaining_usd=remaining,
            budget_used_pct=used_pct,
        )

    async def is_over_budget(self) -> bool:
        """Check if daily budget is exceeded."""
        summary = await self.get_daily_summary()
        return summary.total_cost_usd >= self.daily_budget_usd

    async def get_budget_remaining(self) -> float:
        """Get remaining budget for today."""
        summary = await self.get_daily_summary()
        return summary.budget_remaining_usd

    async def get_weekly_summary(self) -> list[DailyCostSummary]:
        """Get cost summaries for the past 7 days."""
        summaries = []
        for i in range(7):
            date = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
            summary = await self.get_daily_summary(date)
            summaries.append(summary)
        return summaries

    def get_session_costs(self) -> dict[str, Any]:
        """Get costs for current session (in-memory)."""
        total = sum(e.cost_usd for e in self._entries)
        by_agent: dict[str, float] = {}
        by_model: dict[str, float] = {}

        for entry in self._entries:
            by_agent[entry.agent_name] = by_agent.get(entry.agent_name, 0) + entry.cost_usd
            by_model[entry.model] = by_model.get(entry.model, 0) + entry.cost_usd

        return {
            "session_total_usd": total,
            "session_calls": len(self._entries),
            "by_agent": by_agent,
            "by_model": by_model,
        }


# Global instance
_cost_tracker: CostTracker | None = None


def get_cost_tracker() -> CostTracker:
    """Get global cost tracker instance."""
    global _cost_tracker
    if _cost_tracker is None:
        _cost_tracker = CostTracker()
    return _cost_tracker

