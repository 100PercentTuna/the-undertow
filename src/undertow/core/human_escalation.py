"""
Human escalation system.

Routes low-quality or uncertain outputs to human review.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

import structlog

from undertow.services.webhooks import get_webhook_service

logger = structlog.get_logger()


class EscalationReason(str, Enum):
    """Reasons for escalation."""

    QUALITY_GATE_FAILED = "quality_gate_failed"
    LOW_CONFIDENCE = "low_confidence"
    DISPUTED_CLAIMS = "disputed_claims"
    SENSITIVE_TOPIC = "sensitive_topic"
    ADVERSARIAL_CONCERNS = "adversarial_concerns"
    SYSTEM_ERROR = "system_error"
    MANUAL_FLAG = "manual_flag"


class EscalationPriority(str, Enum):
    """Escalation priority levels."""

    CRITICAL = "critical"  # Blocks publication
    HIGH = "high"  # Should review before publication
    MEDIUM = "medium"  # Review when possible
    LOW = "low"  # FYI


class EscalationStatus(str, Enum):
    """Escalation status."""

    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISED = "revised"


@dataclass
class EscalationPackage:
    """
    Complete package for human review.

    Contains all information needed for human decision.
    """

    escalation_id: UUID
    created_at: datetime
    priority: EscalationPriority
    reason: EscalationReason
    status: EscalationStatus

    # What needs review
    story_headline: str
    story_id: str | None
    pipeline_run_id: str | None

    # Analysis results
    quality_score: float
    quality_details: dict[str, float]  # Per-stage scores

    # Specific concerns
    concerns: list[str]
    disputed_claims: list[dict[str, Any]]
    low_confidence_sections: list[str]

    # The content
    draft_content: str | None
    analysis_summary: str | None

    # For review
    reviewer: str | None = None
    review_notes: str | None = None
    resolved_at: datetime | None = None


@dataclass
class EscalationTrigger:
    """Configuration for what triggers escalation."""

    # Quality thresholds
    min_quality_score: float = 0.75
    min_foundation_score: float = 0.75
    min_analysis_score: float = 0.80
    min_adversarial_score: float = 0.80
    min_output_score: float = 0.85

    # Confidence thresholds
    min_overall_confidence: float = 0.70
    max_disputed_claims_pct: float = 0.20

    # Sensitive topics (require review regardless of score)
    sensitive_topics: list[str] = field(default_factory=lambda: [
        "nuclear",
        "assassination",
        "genocide",
        "war crimes",
        "terrorism",
        "coup",
    ])

    # Sensitive zones (higher bar for review)
    sensitive_zones: list[str] = field(default_factory=lambda: [
        "taiwan",
        "korea",
        "iran",
        "russia_core",
        "china",
    ])


class HumanEscalationService:
    """
    Service for managing human escalations.

    Decides when to escalate, creates escalation packages,
    and notifies reviewers.
    """

    def __init__(self, triggers: EscalationTrigger | None = None) -> None:
        """
        Initialize escalation service.

        Args:
            triggers: Escalation trigger configuration
        """
        self.triggers = triggers or EscalationTrigger()
        self._pending_escalations: dict[UUID, EscalationPackage] = {}
        self._webhook_service = get_webhook_service()

    def should_escalate(
        self,
        quality_score: float,
        stage_scores: dict[str, float],
        confidence: float,
        disputed_claims_pct: float,
        content: str,
        zones: list[str],
    ) -> tuple[bool, list[EscalationReason]]:
        """
        Determine if output should be escalated.

        Args:
            quality_score: Overall quality score
            stage_scores: Per-stage quality scores
            confidence: Overall confidence score
            disputed_claims_pct: Percentage of disputed claims
            content: Draft content
            zones: Zones covered

        Returns:
            Tuple of (should_escalate, reasons)
        """
        reasons = []

        # Check quality thresholds
        if quality_score < self.triggers.min_quality_score:
            reasons.append(EscalationReason.QUALITY_GATE_FAILED)

        if stage_scores.get("foundation", 1.0) < self.triggers.min_foundation_score:
            reasons.append(EscalationReason.QUALITY_GATE_FAILED)

        if stage_scores.get("analysis", 1.0) < self.triggers.min_analysis_score:
            reasons.append(EscalationReason.QUALITY_GATE_FAILED)

        if stage_scores.get("adversarial", 1.0) < self.triggers.min_adversarial_score:
            reasons.append(EscalationReason.ADVERSARIAL_CONCERNS)

        # Check confidence
        if confidence < self.triggers.min_overall_confidence:
            reasons.append(EscalationReason.LOW_CONFIDENCE)

        # Check disputed claims
        if disputed_claims_pct > self.triggers.max_disputed_claims_pct:
            reasons.append(EscalationReason.DISPUTED_CLAIMS)

        # Check sensitive topics
        content_lower = content.lower()
        for topic in self.triggers.sensitive_topics:
            if topic in content_lower:
                reasons.append(EscalationReason.SENSITIVE_TOPIC)
                break

        # Check sensitive zones
        for zone in zones:
            if zone in self.triggers.sensitive_zones:
                # Lower threshold for sensitive zones
                if quality_score < self.triggers.min_quality_score + 0.05:
                    reasons.append(EscalationReason.SENSITIVE_TOPIC)
                    break

        # Deduplicate reasons
        reasons = list(set(reasons))

        return len(reasons) > 0, reasons

    async def create_escalation(
        self,
        reason: EscalationReason,
        story_headline: str,
        quality_score: float,
        quality_details: dict[str, float],
        concerns: list[str],
        draft_content: str | None = None,
        analysis_summary: str | None = None,
        story_id: str | None = None,
        pipeline_run_id: str | None = None,
        disputed_claims: list[dict[str, Any]] | None = None,
        low_confidence_sections: list[str] | None = None,
    ) -> EscalationPackage:
        """
        Create an escalation package.

        Args:
            reason: Why escalating
            story_headline: Story being analyzed
            quality_score: Overall quality score
            quality_details: Per-stage scores
            concerns: List of specific concerns
            draft_content: The draft article
            analysis_summary: Summary of analysis
            story_id: Story ID
            pipeline_run_id: Pipeline run ID
            disputed_claims: Any disputed claims
            low_confidence_sections: Low confidence sections

        Returns:
            EscalationPackage
        """
        # Determine priority
        priority = self._determine_priority(reason, quality_score, concerns)

        package = EscalationPackage(
            escalation_id=uuid4(),
            created_at=datetime.utcnow(),
            priority=priority,
            reason=reason,
            status=EscalationStatus.PENDING,
            story_headline=story_headline,
            story_id=story_id,
            pipeline_run_id=pipeline_run_id,
            quality_score=quality_score,
            quality_details=quality_details,
            concerns=concerns,
            disputed_claims=disputed_claims or [],
            low_confidence_sections=low_confidence_sections or [],
            draft_content=draft_content,
            analysis_summary=analysis_summary,
        )

        # Store escalation
        self._pending_escalations[package.escalation_id] = package

        # Notify via webhook
        await self._notify_escalation(package)

        logger.warning(
            "Escalation created",
            escalation_id=str(package.escalation_id),
            reason=reason.value,
            priority=priority.value,
            headline=story_headline[:50],
        )

        return package

    def _determine_priority(
        self,
        reason: EscalationReason,
        quality_score: float,
        concerns: list[str],
    ) -> EscalationPriority:
        """Determine escalation priority."""
        # Critical: System errors or very low quality
        if reason == EscalationReason.SYSTEM_ERROR:
            return EscalationPriority.CRITICAL

        if quality_score < 0.5:
            return EscalationPriority.CRITICAL

        # High: Sensitive topics or adversarial concerns
        if reason in [EscalationReason.SENSITIVE_TOPIC, EscalationReason.ADVERSARIAL_CONCERNS]:
            return EscalationPriority.HIGH

        # Medium: Quality gate failures
        if reason == EscalationReason.QUALITY_GATE_FAILED:
            return EscalationPriority.MEDIUM

        # Low: Everything else
        return EscalationPriority.LOW

    async def _notify_escalation(self, package: EscalationPackage) -> None:
        """Send webhook notification for escalation."""
        try:
            await self._webhook_service.send(
                event="escalation.created",
                payload={
                    "escalation_id": str(package.escalation_id),
                    "priority": package.priority.value,
                    "reason": package.reason.value,
                    "story_headline": package.story_headline,
                    "quality_score": package.quality_score,
                    "concerns": package.concerns[:5],
                },
            )
        except Exception as e:
            logger.error("Failed to send escalation webhook", error=str(e))

    async def resolve_escalation(
        self,
        escalation_id: UUID,
        status: EscalationStatus,
        reviewer: str,
        notes: str,
    ) -> EscalationPackage | None:
        """
        Resolve an escalation.

        Args:
            escalation_id: Escalation to resolve
            status: Resolution status
            reviewer: Who reviewed
            notes: Review notes

        Returns:
            Updated package or None if not found
        """
        package = self._pending_escalations.get(escalation_id)

        if not package:
            return None

        package.status = status
        package.reviewer = reviewer
        package.review_notes = notes
        package.resolved_at = datetime.utcnow()

        logger.info(
            "Escalation resolved",
            escalation_id=str(escalation_id),
            status=status.value,
            reviewer=reviewer,
        )

        return package

    def get_pending_escalations(
        self,
        priority: EscalationPriority | None = None,
    ) -> list[EscalationPackage]:
        """Get pending escalations, optionally filtered by priority."""
        pending = [
            p for p in self._pending_escalations.values()
            if p.status == EscalationStatus.PENDING
        ]

        if priority:
            pending = [p for p in pending if p.priority == priority]

        # Sort by priority and creation time
        priority_order = {
            EscalationPriority.CRITICAL: 0,
            EscalationPriority.HIGH: 1,
            EscalationPriority.MEDIUM: 2,
            EscalationPriority.LOW: 3,
        }

        return sorted(
            pending,
            key=lambda p: (priority_order[p.priority], p.created_at),
        )


# Global instance
_escalation_service: HumanEscalationService | None = None


def get_escalation_service() -> HumanEscalationService:
    """Get global escalation service."""
    global _escalation_service
    if _escalation_service is None:
        _escalation_service = HumanEscalationService()
    return _escalation_service

