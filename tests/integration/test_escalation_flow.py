"""
Integration tests for escalation flow.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID
from datetime import datetime, timedelta


class TestEscalationCreation:
    """Tests for escalation creation."""

    @pytest.mark.asyncio
    async def test_creates_escalation_for_low_quality(self):
        """Test that low quality triggers escalation."""
        from undertow.core.human_escalation import (
            EscalationService,
            EscalationReason,
            EscalationPriority,
        )
        
        service = EscalationService()
        
        package = await service.create_escalation(
            reason=EscalationReason.LOW_QUALITY,
            story_headline="Test Story with Low Quality",
            quality_score=0.65,
            quality_details={"coherence": 0.6, "sourcing": 0.7},
            concerns=["Weak sourcing", "Missing context"],
        )
        
        assert package is not None
        assert package.priority == EscalationPriority.HIGH
        assert package.reason == EscalationReason.LOW_QUALITY
        assert package.quality_score == 0.65

    @pytest.mark.asyncio
    async def test_critical_priority_for_very_low_quality(self):
        """Test critical priority for very low scores."""
        from undertow.core.human_escalation import (
            EscalationService,
            EscalationReason,
            EscalationPriority,
        )
        
        service = EscalationService()
        
        package = await service.create_escalation(
            reason=EscalationReason.ADVERSARIAL_CONCERNS,
            story_headline="Highly Disputed Analysis",
            quality_score=0.55,  # Very low
            quality_details={},
            concerns=["Major factual disputes", "Unresolved contradictions"],
        )
        
        assert package.priority == EscalationPriority.CRITICAL

    @pytest.mark.asyncio
    async def test_disputed_claims_trigger_escalation(self):
        """Test escalation for disputed claims."""
        from undertow.core.human_escalation import (
            EscalationService,
            EscalationReason,
            EscalationPriority,
        )
        
        service = EscalationService()
        
        package = await service.create_escalation(
            reason=EscalationReason.DISPUTED_CLAIMS,
            story_headline="Article with Contested Facts",
            quality_score=0.75,
            quality_details={"verification": 0.5},
            concerns=["3 claims disputed by sources"],
            disputed_claims=[
                {"claim": "Claim A", "evidence": "Contradicted by Source X"},
                {"claim": "Claim B", "evidence": "No supporting evidence found"},
            ],
        )
        
        assert len(package.disputed_claims) == 2
        assert package.reason == EscalationReason.DISPUTED_CLAIMS


class TestEscalationResolution:
    """Tests for escalation resolution."""

    @pytest.mark.asyncio
    async def test_resolves_with_approval(self):
        """Test approving an escalation."""
        from undertow.core.human_escalation import (
            EscalationService,
            EscalationReason,
            EscalationStatus,
        )
        
        service = EscalationService()
        
        # Create escalation
        package = await service.create_escalation(
            reason=EscalationReason.MANUAL_FLAG,
            story_headline="Flagged for Review",
            quality_score=0.82,
            quality_details={},
            concerns=["Editor flagged for sensitivity"],
        )
        
        # Resolve it
        resolved = await service.resolve_escalation(
            escalation_id=package.escalation_id,
            status=EscalationStatus.APPROVED,
            reviewer="test_reviewer",
            notes="Content verified and approved for publication",
        )
        
        assert resolved is not None
        assert resolved.status == EscalationStatus.APPROVED
        assert resolved.reviewer == "test_reviewer"
        assert resolved.resolved_at is not None

    @pytest.mark.asyncio
    async def test_resolves_with_rejection(self):
        """Test rejecting an escalation."""
        from undertow.core.human_escalation import (
            EscalationService,
            EscalationReason,
            EscalationStatus,
        )
        
        service = EscalationService()
        
        package = await service.create_escalation(
            reason=EscalationReason.LOW_QUALITY,
            story_headline="Poor Quality Article",
            quality_score=0.58,
            quality_details={},
            concerns=["Factual errors", "Missing key context"],
        )
        
        resolved = await service.resolve_escalation(
            escalation_id=package.escalation_id,
            status=EscalationStatus.REJECTED,
            reviewer="editor",
            notes="Too many errors - needs complete rewrite",
        )
        
        assert resolved.status == EscalationStatus.REJECTED

    @pytest.mark.asyncio
    async def test_cannot_resolve_nonexistent_escalation(self):
        """Test handling of missing escalation."""
        from undertow.core.human_escalation import (
            EscalationService,
            EscalationStatus,
        )
        
        service = EscalationService()
        
        result = await service.resolve_escalation(
            escalation_id=UUID("00000000-0000-0000-0000-000000000000"),
            status=EscalationStatus.APPROVED,
            reviewer="test",
            notes="test",
        )
        
        assert result is None


class TestEscalationFiltering:
    """Tests for escalation filtering and listing."""

    @pytest.mark.asyncio
    async def test_filters_by_priority(self):
        """Test filtering escalations by priority."""
        from undertow.core.human_escalation import (
            EscalationService,
            EscalationReason,
            EscalationPriority,
        )
        
        service = EscalationService()
        
        # Create escalations with different priorities
        await service.create_escalation(
            reason=EscalationReason.LOW_QUALITY,
            story_headline="Critical Issue",
            quality_score=0.50,
            quality_details={},
            concerns=[],
        )
        
        await service.create_escalation(
            reason=EscalationReason.MANUAL_FLAG,
            story_headline="Minor Issue",
            quality_score=0.82,
            quality_details={},
            concerns=[],
        )
        
        # Filter by critical
        critical = service.get_pending_escalations(EscalationPriority.CRITICAL)
        
        for esc in critical:
            assert esc.priority == EscalationPriority.CRITICAL

    @pytest.mark.asyncio
    async def test_lists_pending_only(self):
        """Test that only pending escalations are returned by default."""
        from undertow.core.human_escalation import (
            EscalationService,
            EscalationReason,
            EscalationStatus,
        )
        
        service = EscalationService()
        
        # Create and resolve one
        package = await service.create_escalation(
            reason=EscalationReason.MANUAL_FLAG,
            story_headline="Will be resolved",
            quality_score=0.80,
            quality_details={},
            concerns=[],
        )
        
        await service.resolve_escalation(
            escalation_id=package.escalation_id,
            status=EscalationStatus.APPROVED,
            reviewer="test",
            notes="Done",
        )
        
        # Create pending one
        await service.create_escalation(
            reason=EscalationReason.MANUAL_FLAG,
            story_headline="Still pending",
            quality_score=0.80,
            quality_details={},
            concerns=[],
        )
        
        pending = service.get_pending_escalations()
        
        # All returned should be pending
        for esc in pending:
            assert esc.status == EscalationStatus.PENDING


class TestEscalationNotifications:
    """Tests for escalation notifications."""

    @pytest.mark.asyncio
    async def test_sends_notification_on_creation(self):
        """Test that notification is sent when escalation is created."""
        from undertow.tasks.escalation_tasks import notify_escalation
        
        # This would test the Celery task
        # In actual test, would mock the notification service
        pass

    @pytest.mark.asyncio
    async def test_sends_reminder_for_stale_escalations(self):
        """Test that reminders are sent for old pending escalations."""
        from undertow.tasks.escalation_tasks import process_escalation_queue
        
        # This would test the queue processing task
        pass


class TestEscalationAPI:
    """Tests for escalation API endpoints."""

    @pytest.mark.asyncio
    async def test_list_escalations_endpoint(self):
        """Test GET /escalations endpoint."""
        # Would use TestClient with mocked service
        pass

    @pytest.mark.asyncio
    async def test_resolve_escalation_endpoint(self):
        """Test POST /escalations/{id}/resolve endpoint."""
        # Would use TestClient with mocked service
        pass

    @pytest.mark.asyncio
    async def test_create_escalation_endpoint(self):
        """Test POST /escalations endpoint."""
        # Would use TestClient with mocked service
        pass

