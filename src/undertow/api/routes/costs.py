"""
Cost tracking API routes.
"""

from typing import Any

from fastapi import APIRouter, Depends

from undertow.api.middleware.auth import require_auth
from undertow.services.cost_tracker import get_cost_tracker, DailyCostSummary

router = APIRouter(prefix="/costs", tags=["Costs"])


@router.get("", response_model=dict)
async def get_current_costs() -> dict[str, Any]:
    """
    Get current day's cost summary.

    Returns budget usage, costs by agent and model.
    """
    tracker = get_cost_tracker()
    summary = await tracker.get_daily_summary()

    return {
        "date": summary.date,
        "total_cost_usd": round(summary.total_cost_usd, 4),
        "total_calls": summary.total_calls,
        "budget_usd": summary.budget_usd,
        "budget_remaining_usd": round(summary.budget_remaining_usd, 4),
        "budget_used_pct": round(summary.budget_used_pct, 2),
        "by_agent": {k: round(v, 4) for k, v in summary.by_agent.items()},
        "by_model": {k: round(v, 4) for k, v in summary.by_model.items()},
    }


@router.get("/weekly", response_model=list)
async def get_weekly_costs() -> list[dict[str, Any]]:
    """
    Get cost summaries for the past 7 days.
    """
    tracker = get_cost_tracker()
    summaries = await tracker.get_weekly_summary()

    return [
        {
            "date": s.date,
            "total_cost_usd": round(s.total_cost_usd, 4),
            "total_calls": s.total_calls,
            "budget_used_pct": round(s.budget_used_pct, 2),
        }
        for s in summaries
    ]


@router.get("/session", response_model=dict)
async def get_session_costs() -> dict[str, Any]:
    """
    Get costs for current session (since server start).
    """
    tracker = get_cost_tracker()
    return tracker.get_session_costs()


@router.get("/budget", response_model=dict)
async def get_budget_status() -> dict[str, Any]:
    """
    Get current budget status.

    Returns whether over budget and remaining amount.
    """
    tracker = get_cost_tracker()

    is_over = await tracker.is_over_budget()
    remaining = await tracker.get_budget_remaining()

    return {
        "is_over_budget": is_over,
        "budget_remaining_usd": round(remaining, 4),
        "daily_budget_usd": tracker.daily_budget_usd,
    }

