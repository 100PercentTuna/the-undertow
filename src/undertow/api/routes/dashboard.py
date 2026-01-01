"""
Dashboard API routes.

Provides real-time statistics and overview data for the admin dashboard.
"""

from typing import Any
from datetime import datetime, timedelta

from fastapi import APIRouter

from undertow.services.cost_tracker import get_cost_tracker
from undertow.core.human_escalation import get_escalation_service, EscalationStatus
from undertow.infrastructure.audit import get_audit_logger, AuditAction

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats")
async def get_dashboard_stats() -> dict[str, Any]:
    """
    Get overview statistics for the dashboard.
    
    Returns real-time metrics across all system components.
    """
    cost_tracker = get_cost_tracker()
    escalation_service = get_escalation_service()
    audit_logger = get_audit_logger()
    
    # Cost stats
    cost_summary = cost_tracker.get_summary()
    
    # Escalation stats
    pending_escalations = escalation_service.get_pending_escalations()
    critical_escalations = sum(1 for e in pending_escalations if e.priority.value == "critical")
    
    # Recent activity from audit log
    recent_events = audit_logger.get_recent_events(limit=100)
    
    # Count events by type
    articles_today = sum(
        1 for e in recent_events
        if e.action == AuditAction.ARTICLE_GENERATED
        and e.timestamp.date() == datetime.utcnow().date()
    )
    
    pipelines_today = sum(
        1 for e in recent_events
        if e.action == AuditAction.PIPELINE_COMPLETED
        and e.timestamp.date() == datetime.utcnow().date()
    )
    
    errors_today = sum(
        1 for e in recent_events
        if e.severity.value == "error"
        and e.timestamp.date() == datetime.utcnow().date()
    )
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "costs": {
            "today": cost_summary["today"],
            "week": cost_summary["week"],
            "month": cost_summary["month"],
            "budget_remaining": cost_summary["budget_remaining"],
            "budget_percentage": min(100, (cost_summary["today"] / 50) * 100),
        },
        "escalations": {
            "pending": len(pending_escalations),
            "critical": critical_escalations,
        },
        "activity": {
            "articles_today": articles_today,
            "pipelines_today": pipelines_today,
            "errors_today": errors_today,
        },
        "health": {
            "status": "healthy" if errors_today < 5 else "degraded",
            "uptime_hours": 24,  # Placeholder
        },
    }


@router.get("/activity")
async def get_recent_activity(
    limit: int = 50,
) -> dict[str, Any]:
    """
    Get recent system activity.
    """
    audit_logger = get_audit_logger()
    events = audit_logger.get_recent_events(limit=limit)
    
    return {
        "events": [
            {
                "id": str(e.id),
                "timestamp": e.timestamp.isoformat(),
                "action": e.action.value,
                "severity": e.severity.value,
                "actor": e.actor,
                "resource_type": e.resource_type,
                "resource_id": e.resource_id,
                "success": e.success,
                "details": e.details,
            }
            for e in reversed(events)
        ],
        "total": len(events),
    }


@router.get("/costs/chart")
async def get_cost_chart_data(
    days: int = 7,
) -> dict[str, Any]:
    """
    Get cost data for charting.
    """
    cost_tracker = get_cost_tracker()
    
    # Generate mock data for chart (would be real DB query in production)
    today = datetime.utcnow().date()
    chart_data = []
    
    for i in range(days - 1, -1, -1):
        date = today - timedelta(days=i)
        # In production, query actual costs by date
        chart_data.append({
            "date": date.isoformat(),
            "cost": cost_tracker.get_summary()["today"] / days if i == 0 else 0,
        })
    
    return {
        "period_days": days,
        "data": chart_data,
        "total": sum(d["cost"] for d in chart_data),
    }


@router.get("/pipeline/recent")
async def get_recent_pipeline_runs(
    limit: int = 10,
) -> dict[str, Any]:
    """
    Get recent pipeline runs.
    """
    audit_logger = get_audit_logger()
    
    # Get pipeline events
    completed = audit_logger.get_recent_events(
        limit=limit * 2,
        action=AuditAction.PIPELINE_COMPLETED,
    )
    
    failed = audit_logger.get_recent_events(
        limit=limit,
        action=AuditAction.PIPELINE_FAILED,
    )
    
    # Combine and sort
    all_runs = []
    
    for e in completed:
        all_runs.append({
            "run_id": e.resource_id,
            "status": "completed",
            "timestamp": e.timestamp.isoformat(),
            "duration_ms": e.duration_ms,
            "articles": e.details.get("articles_generated", 0),
            "cost": e.details.get("total_cost_usd", 0),
        })
    
    for e in failed:
        all_runs.append({
            "run_id": e.resource_id,
            "status": "failed",
            "timestamp": e.timestamp.isoformat(),
            "stage": e.details.get("stage", "unknown"),
            "error": e.error,
        })
    
    # Sort by timestamp descending
    all_runs.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return {
        "runs": all_runs[:limit],
        "total_completed": len(completed),
        "total_failed": len(failed),
    }


@router.get("/agents/performance")
async def get_agent_performance() -> dict[str, Any]:
    """
    Get agent performance metrics.
    """
    cost_tracker = get_cost_tracker()
    breakdown = cost_tracker.get_breakdown_by_agent()
    
    agents = []
    for agent_name, data in breakdown.items():
        agents.append({
            "name": agent_name,
            "calls": data["calls"],
            "total_cost": data["cost"],
            "avg_cost_per_call": data["cost"] / data["calls"] if data["calls"] > 0 else 0,
        })
    
    # Sort by cost descending
    agents.sort(key=lambda x: x["total_cost"], reverse=True)
    
    return {
        "agents": agents,
        "total_calls": sum(a["calls"] for a in agents),
        "total_cost": sum(a["total_cost"] for a in agents),
    }


@router.get("/zones/coverage")
async def get_zone_coverage() -> dict[str, Any]:
    """
    Get coverage statistics by zone.
    """
    from undertow.infrastructure.seeders import get_all_zones
    
    zones = get_all_zones()
    
    # Group by region
    by_region: dict[str, list[dict]] = {}
    for zone in zones:
        region = zone["region"]
        if region not in by_region:
            by_region[region] = []
        by_region[region].append({
            "id": zone["id"],
            "name": zone["name"],
            "countries_count": len(zone["countries"]),
            # In production, would include article counts, last updated, etc.
            "articles_this_week": 0,
            "last_article": None,
        })
    
    return {
        "total_zones": len(zones),
        "by_region": by_region,
    }


@router.get("/quality/summary")
async def get_quality_summary() -> dict[str, Any]:
    """
    Get quality metrics summary.
    """
    escalation_service = get_escalation_service()
    all_escalations = list(escalation_service._pending_escalations.values())
    
    # Calculate metrics
    total = len(all_escalations)
    if total == 0:
        return {
            "avg_quality_score": 0.85,
            "escalation_rate": 0,
            "approval_rate": 1.0,
            "by_reason": {},
        }
    
    avg_quality = sum(e.quality_score for e in all_escalations) / total
    
    resolved = [e for e in all_escalations if e.status != EscalationStatus.PENDING]
    approved = sum(1 for e in resolved if e.status == EscalationStatus.APPROVED)
    approval_rate = approved / len(resolved) if resolved else 1.0
    
    by_reason: dict[str, int] = {}
    for e in all_escalations:
        reason = e.reason.value
        by_reason[reason] = by_reason.get(reason, 0) + 1
    
    return {
        "avg_quality_score": avg_quality,
        "escalation_rate": total / 100,  # Placeholder
        "approval_rate": approval_rate,
        "by_reason": by_reason,
    }

