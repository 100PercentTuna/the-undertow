"""
Audit logging system for The Undertow.

Tracks all significant operations for compliance and debugging.
"""

import structlog
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4
import json

logger = structlog.get_logger(__name__)


class AuditAction(str, Enum):
    """Types of auditable actions."""
    
    # Story actions
    STORY_CREATED = "story.created"
    STORY_UPDATED = "story.updated"
    STORY_DELETED = "story.deleted"
    STORY_ANALYZED = "story.analyzed"
    
    # Article actions
    ARTICLE_GENERATED = "article.generated"
    ARTICLE_EDITED = "article.edited"
    ARTICLE_APPROVED = "article.approved"
    ARTICLE_REJECTED = "article.rejected"
    ARTICLE_PUBLISHED = "article.published"
    
    # Pipeline actions
    PIPELINE_STARTED = "pipeline.started"
    PIPELINE_COMPLETED = "pipeline.completed"
    PIPELINE_FAILED = "pipeline.failed"
    PIPELINE_STAGE_COMPLETED = "pipeline.stage_completed"
    
    # Escalation actions
    ESCALATION_CREATED = "escalation.created"
    ESCALATION_RESOLVED = "escalation.resolved"
    ESCALATION_REASSIGNED = "escalation.reassigned"
    
    # Verification actions
    CLAIMS_EXTRACTED = "verification.claims_extracted"
    CLAIMS_VERIFIED = "verification.claims_verified"
    
    # RAG actions
    DOCUMENT_INDEXED = "rag.document_indexed"
    DOCUMENT_DELETED = "rag.document_deleted"
    SEARCH_PERFORMED = "rag.search_performed"
    
    # User actions
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    SETTINGS_CHANGED = "settings.changed"
    
    # System actions
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    BUDGET_WARNING = "system.budget_warning"
    BUDGET_EXCEEDED = "system.budget_exceeded"
    
    # LLM actions
    LLM_CALL = "llm.call"
    LLM_ERROR = "llm.error"
    LLM_RATE_LIMITED = "llm.rate_limited"


class AuditSeverity(str, Enum):
    """Severity levels for audit events."""
    
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """A single audit event."""
    
    id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    action: AuditAction = AuditAction.STORY_CREATED
    severity: AuditSeverity = AuditSeverity.INFO
    actor: str | None = None  # User or system component
    resource_type: str | None = None  # story, article, pipeline, etc.
    resource_id: str | None = None
    details: dict[str, Any] = field(default_factory=dict)
    ip_address: str | None = None
    user_agent: str | None = None
    duration_ms: int | None = None
    success: bool = True
    error: str | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": str(self.id),
            "timestamp": self.timestamp.isoformat(),
            "action": self.action.value,
            "severity": self.severity.value,
            "actor": self.actor,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "details": self.details,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "duration_ms": self.duration_ms,
            "success": self.success,
            "error": self.error,
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


class AuditLogger:
    """
    Audit logging service.
    
    Logs all significant operations for compliance and debugging.
    Supports multiple backends (log file, database, external service).
    """
    
    def __init__(self) -> None:
        self._events: list[AuditEvent] = []
        self._max_memory_events = 1000
    
    def log(
        self,
        action: AuditAction,
        severity: AuditSeverity = AuditSeverity.INFO,
        actor: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        details: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        duration_ms: int | None = None,
        success: bool = True,
        error: str | None = None,
    ) -> AuditEvent:
        """
        Log an audit event.
        
        Args:
            action: Type of action being logged
            severity: Severity level
            actor: User or system component performing the action
            resource_type: Type of resource being affected
            resource_id: ID of the resource
            details: Additional details
            ip_address: Client IP address
            user_agent: Client user agent
            duration_ms: Duration of operation in milliseconds
            success: Whether the operation succeeded
            error: Error message if failed
            
        Returns:
            The created audit event
        """
        event = AuditEvent(
            action=action,
            severity=severity,
            actor=actor,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
            duration_ms=duration_ms,
            success=success,
            error=error,
        )
        
        # Store in memory (circular buffer)
        self._events.append(event)
        if len(self._events) > self._max_memory_events:
            self._events = self._events[-self._max_memory_events:]
        
        # Log to structured logger
        log_method = {
            AuditSeverity.DEBUG: logger.debug,
            AuditSeverity.INFO: logger.info,
            AuditSeverity.WARNING: logger.warning,
            AuditSeverity.ERROR: logger.error,
            AuditSeverity.CRITICAL: logger.critical,
        }.get(severity, logger.info)
        
        log_method(
            "audit_event",
            action=action.value,
            actor=actor,
            resource_type=resource_type,
            resource_id=resource_id,
            success=success,
            **details or {},
        )
        
        return event
    
    def log_story_created(
        self,
        story_id: str,
        headline: str,
        actor: str | None = None,
    ) -> AuditEvent:
        """Log story creation."""
        return self.log(
            action=AuditAction.STORY_CREATED,
            actor=actor,
            resource_type="story",
            resource_id=story_id,
            details={"headline": headline[:100]},
        )
    
    def log_article_generated(
        self,
        article_id: str,
        story_id: str,
        quality_score: float,
        cost: float,
        duration_ms: int,
    ) -> AuditEvent:
        """Log article generation."""
        return self.log(
            action=AuditAction.ARTICLE_GENERATED,
            resource_type="article",
            resource_id=article_id,
            duration_ms=duration_ms,
            details={
                "story_id": story_id,
                "quality_score": quality_score,
                "cost_usd": cost,
            },
        )
    
    def log_pipeline_started(
        self,
        run_id: str,
        story_count: int,
    ) -> AuditEvent:
        """Log pipeline start."""
        return self.log(
            action=AuditAction.PIPELINE_STARTED,
            resource_type="pipeline",
            resource_id=run_id,
            details={"story_count": story_count},
        )
    
    def log_pipeline_completed(
        self,
        run_id: str,
        articles_generated: int,
        total_cost: float,
        duration_ms: int,
    ) -> AuditEvent:
        """Log pipeline completion."""
        return self.log(
            action=AuditAction.PIPELINE_COMPLETED,
            resource_type="pipeline",
            resource_id=run_id,
            duration_ms=duration_ms,
            details={
                "articles_generated": articles_generated,
                "total_cost_usd": total_cost,
            },
        )
    
    def log_pipeline_failed(
        self,
        run_id: str,
        stage: str,
        error: str,
    ) -> AuditEvent:
        """Log pipeline failure."""
        return self.log(
            action=AuditAction.PIPELINE_FAILED,
            severity=AuditSeverity.ERROR,
            resource_type="pipeline",
            resource_id=run_id,
            success=False,
            error=error,
            details={"stage": stage},
        )
    
    def log_escalation_created(
        self,
        escalation_id: str,
        reason: str,
        priority: str,
        story_headline: str,
    ) -> AuditEvent:
        """Log escalation creation."""
        return self.log(
            action=AuditAction.ESCALATION_CREATED,
            severity=AuditSeverity.WARNING,
            resource_type="escalation",
            resource_id=escalation_id,
            details={
                "reason": reason,
                "priority": priority,
                "story_headline": story_headline[:100],
            },
        )
    
    def log_escalation_resolved(
        self,
        escalation_id: str,
        status: str,
        reviewer: str,
    ) -> AuditEvent:
        """Log escalation resolution."""
        return self.log(
            action=AuditAction.ESCALATION_RESOLVED,
            actor=reviewer,
            resource_type="escalation",
            resource_id=escalation_id,
            details={"status": status},
        )
    
    def log_llm_call(
        self,
        provider: str,
        model: str,
        tokens_in: int,
        tokens_out: int,
        cost: float,
        duration_ms: int,
        agent: str | None = None,
    ) -> AuditEvent:
        """Log LLM API call."""
        return self.log(
            action=AuditAction.LLM_CALL,
            severity=AuditSeverity.DEBUG,
            actor=agent,
            duration_ms=duration_ms,
            details={
                "provider": provider,
                "model": model,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "cost_usd": cost,
            },
        )
    
    def log_budget_warning(
        self,
        current_spend: float,
        daily_budget: float,
        percentage: float,
    ) -> AuditEvent:
        """Log budget warning."""
        return self.log(
            action=AuditAction.BUDGET_WARNING,
            severity=AuditSeverity.WARNING,
            details={
                "current_spend": current_spend,
                "daily_budget": daily_budget,
                "percentage": percentage,
            },
        )
    
    def get_recent_events(
        self,
        limit: int = 100,
        action: AuditAction | None = None,
        severity: AuditSeverity | None = None,
    ) -> list[AuditEvent]:
        """Get recent audit events."""
        events = self._events.copy()
        
        if action:
            events = [e for e in events if e.action == action]
        
        if severity:
            events = [e for e in events if e.severity == severity]
        
        return events[-limit:]
    
    def get_events_for_resource(
        self,
        resource_type: str,
        resource_id: str,
    ) -> list[AuditEvent]:
        """Get all events for a specific resource."""
        return [
            e for e in self._events
            if e.resource_type == resource_type and e.resource_id == resource_id
        ]


# Singleton instance
_audit_logger: AuditLogger | None = None


def get_audit_logger() -> AuditLogger:
    """Get or create the audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


# Convenience function
def audit(
    action: AuditAction,
    **kwargs: Any,
) -> AuditEvent:
    """Log an audit event using the global logger."""
    return get_audit_logger().log(action, **kwargs)

