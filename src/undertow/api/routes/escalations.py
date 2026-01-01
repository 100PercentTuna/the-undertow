"""
Human escalation API routes.

Provides endpoints for managing escalations requiring human review.
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from undertow.core.human_escalation import (
    get_escalation_service,
    EscalationPriority,
    EscalationStatus,
    EscalationReason,
)

router = APIRouter(prefix="/escalations", tags=["Escalations"])


class EscalationResponse(BaseModel):
    """Response for a single escalation."""

    escalation_id: str
    priority: str
    reason: str
    status: str
    story_headline: str
    quality_score: float
    concerns: list[str]
    created_at: str
    reviewer: str | None
    resolved_at: str | None


class EscalationListResponse(BaseModel):
    """Response for escalation list."""

    total: int
    pending: int
    escalations: list[EscalationResponse]


class ResolveEscalationRequest(BaseModel):
    """Request to resolve an escalation."""

    status: str = Field(..., description="approved, rejected, or revised")
    reviewer: str = Field(..., min_length=1)
    notes: str = Field(..., min_length=10)


class CreateEscalationRequest(BaseModel):
    """Request to create an escalation."""

    reason: str
    story_headline: str
    quality_score: float = Field(..., ge=0, le=1)
    concerns: list[str]
    draft_content: str | None = None
    analysis_summary: str | None = None
    story_id: str | None = None
    pipeline_run_id: str | None = None


@router.get("", response_model=EscalationListResponse)
async def list_escalations(
    status: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    limit: int = Query(default=50, le=100),
) -> EscalationListResponse:
    """
    List escalations.

    Filter by status (pending, in_review, approved, rejected, revised)
    or priority (critical, high, medium, low).
    """
    service = get_escalation_service()

    # Get pending escalations
    priority_filter = EscalationPriority(priority) if priority else None
    pending = service.get_pending_escalations(priority_filter)

    # Convert to response
    escalations = [
        EscalationResponse(
            escalation_id=str(e.escalation_id),
            priority=e.priority.value,
            reason=e.reason.value,
            status=e.status.value,
            story_headline=e.story_headline,
            quality_score=e.quality_score,
            concerns=e.concerns[:5],
            created_at=e.created_at.isoformat(),
            reviewer=e.reviewer,
            resolved_at=e.resolved_at.isoformat() if e.resolved_at else None,
        )
        for e in pending[:limit]
    ]

    return EscalationListResponse(
        total=len(pending),
        pending=sum(1 for e in pending if e.status == EscalationStatus.PENDING),
        escalations=escalations,
    )


@router.get("/{escalation_id}")
async def get_escalation(escalation_id: UUID) -> dict[str, Any]:
    """
    Get detailed information about an escalation.
    """
    service = get_escalation_service()

    # Find escalation
    package = service._pending_escalations.get(escalation_id)

    if not package:
        raise HTTPException(status_code=404, detail="Escalation not found")

    return {
        "escalation_id": str(package.escalation_id),
        "priority": package.priority.value,
        "reason": package.reason.value,
        "status": package.status.value,
        "story_headline": package.story_headline,
        "story_id": package.story_id,
        "pipeline_run_id": package.pipeline_run_id,
        "quality_score": package.quality_score,
        "quality_details": package.quality_details,
        "concerns": package.concerns,
        "disputed_claims": package.disputed_claims,
        "low_confidence_sections": package.low_confidence_sections,
        "draft_content": package.draft_content,
        "analysis_summary": package.analysis_summary,
        "reviewer": package.reviewer,
        "review_notes": package.review_notes,
        "created_at": package.created_at.isoformat(),
        "resolved_at": package.resolved_at.isoformat() if package.resolved_at else None,
    }


@router.post("/{escalation_id}/resolve")
async def resolve_escalation(
    escalation_id: UUID,
    request: ResolveEscalationRequest,
) -> dict[str, Any]:
    """
    Resolve an escalation.

    Status options:
    - approved: Content is approved for publication
    - rejected: Content is rejected, needs rewrite
    - revised: Content was revised and is now approved
    """
    service = get_escalation_service()

    try:
        status = EscalationStatus(request.status)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: approved, rejected, revised",
        )

    package = await service.resolve_escalation(
        escalation_id=escalation_id,
        status=status,
        reviewer=request.reviewer,
        notes=request.notes,
    )

    if not package:
        raise HTTPException(status_code=404, detail="Escalation not found")

    return {
        "escalation_id": str(package.escalation_id),
        "status": package.status.value,
        "reviewer": package.reviewer,
        "resolved_at": package.resolved_at.isoformat() if package.resolved_at else None,
        "message": f"Escalation {request.status} by {request.reviewer}",
    }


@router.post("")
async def create_escalation(request: CreateEscalationRequest) -> dict[str, Any]:
    """
    Manually create an escalation.

    Useful for flagging content that needs review.
    """
    service = get_escalation_service()

    try:
        reason = EscalationReason(request.reason)
    except ValueError:
        reason = EscalationReason.MANUAL_FLAG

    package = await service.create_escalation(
        reason=reason,
        story_headline=request.story_headline,
        quality_score=request.quality_score,
        quality_details={},
        concerns=request.concerns,
        draft_content=request.draft_content,
        analysis_summary=request.analysis_summary,
        story_id=request.story_id,
        pipeline_run_id=request.pipeline_run_id,
    )

    return {
        "escalation_id": str(package.escalation_id),
        "priority": package.priority.value,
        "status": package.status.value,
        "message": "Escalation created",
    }


@router.get("/stats/summary")
async def get_escalation_stats() -> dict[str, Any]:
    """
    Get escalation statistics.
    """
    service = get_escalation_service()

    all_escalations = list(service._pending_escalations.values())

    by_status = {}
    by_priority = {}
    by_reason = {}

    for e in all_escalations:
        by_status[e.status.value] = by_status.get(e.status.value, 0) + 1
        by_priority[e.priority.value] = by_priority.get(e.priority.value, 0) + 1
        by_reason[e.reason.value] = by_reason.get(e.reason.value, 0) + 1

    return {
        "total": len(all_escalations),
        "by_status": by_status,
        "by_priority": by_priority,
        "by_reason": by_reason,
    }

