"""
Celery tasks for escalation operations.

Handles notifications and escalation management.
"""

import structlog
from celery import shared_task
from typing import Any
from uuid import UUID

from undertow.tasks.celery_app import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(name="undertow.notify_escalation")
def notify_escalation(
    escalation_id: str,
    priority: str,
    story_headline: str,
    quality_score: float,
    concerns: list[str],
) -> dict[str, Any]:
    """
    Send notification for a new escalation.
    
    Sends email and/or Slack notification to reviewers.
    
    Args:
        escalation_id: UUID of the escalation
        priority: Priority level (critical, high, medium, low)
        story_headline: Story being escalated
        quality_score: Quality score that triggered escalation
        concerns: List of concerns
        
    Returns:
        Notification status
    """
    import asyncio
    
    async def _run() -> dict[str, Any]:
        from undertow.config import get_settings
        from undertow.services.webhooks import WebhookService
        
        settings = get_settings()
        
        notifications_sent = []
        
        # Send webhook notification
        try:
            webhook_service = WebhookService()
            await webhook_service.send(
                event_type="escalation.created",
                payload={
                    "escalation_id": escalation_id,
                    "priority": priority,
                    "story_headline": story_headline,
                    "quality_score": quality_score,
                    "concerns": concerns[:5],
                    "review_url": f"{settings.app_url}/escalations/{escalation_id}",
                },
            )
            notifications_sent.append("webhook")
        except Exception as e:
            logger.error("webhook_notification_failed", error=str(e))
        
        # Send email for high-priority escalations
        if priority in ("critical", "high"):
            try:
                await _send_escalation_email(
                    escalation_id=escalation_id,
                    priority=priority,
                    story_headline=story_headline,
                    quality_score=quality_score,
                    concerns=concerns,
                )
                notifications_sent.append("email")
            except Exception as e:
                logger.error("email_notification_failed", error=str(e))
        
        logger.info(
            "escalation_notifications_sent",
            escalation_id=escalation_id,
            priority=priority,
            notifications=notifications_sent,
        )
        
        return {
            "escalation_id": escalation_id,
            "notifications_sent": notifications_sent,
        }
    
    return asyncio.run(_run())


async def _send_escalation_email(
    escalation_id: str,
    priority: str,
    story_headline: str,
    quality_score: float,
    concerns: list[str],
) -> None:
    """Send escalation email notification."""
    from undertow.config import get_settings
    import httpx
    
    settings = get_settings()
    
    if not settings.sendgrid_api_key:
        logger.warning("sendgrid_not_configured")
        return
    
    priority_emoji = {
        "critical": "🚨",
        "high": "⚠️",
        "medium": "📋",
        "low": "📝",
    }.get(priority, "📋")
    
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: #1a1a2e; color: #fff; padding: 20px; text-align: center;">
            <h1 style="color: #f59e0b; margin: 0;">The Undertow</h1>
            <p style="color: #94a3b8; margin: 5px 0 0;">Human Review Required</p>
        </div>
        
        <div style="padding: 20px; background: #f8fafc;">
            <h2 style="color: #1e293b;">{priority_emoji} {priority.upper()} Priority Escalation</h2>
            
            <div style="background: #fff; padding: 15px; border-radius: 8px; margin: 15px 0;">
                <p style="font-weight: bold; margin: 0 0 10px;">Story:</p>
                <p style="margin: 0; color: #475569;">{story_headline}</p>
            </div>
            
            <div style="background: #fff; padding: 15px; border-radius: 8px; margin: 15px 0;">
                <p style="font-weight: bold; margin: 0 0 10px;">Quality Score: {quality_score:.0%}</p>
            </div>
            
            <div style="background: #fff; padding: 15px; border-radius: 8px; margin: 15px 0;">
                <p style="font-weight: bold; margin: 0 0 10px;">Concerns:</p>
                <ul style="margin: 0; padding-left: 20px; color: #dc2626;">
                    {''.join(f'<li>{c}</li>' for c in concerns[:5])}
                </ul>
            </div>
            
            <div style="text-align: center; margin-top: 20px;">
                <a href="{settings.app_url}/escalations/{escalation_id}" 
                   style="display: inline-block; background: #f59e0b; color: #1a1a2e; 
                          padding: 12px 24px; text-decoration: none; border-radius: 6px;
                          font-weight: bold;">
                    Review Now →
                </a>
            </div>
        </div>
        
        <div style="padding: 15px; text-align: center; color: #94a3b8; font-size: 12px;">
            <p>This is an automated notification from The Undertow.</p>
        </div>
    </body>
    </html>
    """
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={
                "Authorization": f"Bearer {settings.sendgrid_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "personalizations": [
                    {"to": [{"email": settings.alert_email}]}
                ],
                "from": {"email": settings.from_email, "name": "The Undertow"},
                "subject": f"{priority_emoji} [{priority.upper()}] Escalation: {story_headline[:50]}...",
                "content": [
                    {"type": "text/html", "value": html_content}
                ],
            },
        )
        
        if response.status_code >= 400:
            raise Exception(f"SendGrid error: {response.status_code}")


@celery_app.task(name="undertow.process_escalation_queue")
def process_escalation_queue() -> dict[str, Any]:
    """
    Process pending escalations and send reminder notifications.
    
    Run periodically to remind reviewers of pending escalations.
    
    Returns:
        Processing summary
    """
    import asyncio
    from datetime import datetime, timedelta
    
    async def _run() -> dict[str, Any]:
        from undertow.core.human_escalation import get_escalation_service, EscalationPriority
        
        service = get_escalation_service()
        
        # Get pending escalations
        pending = service.get_pending_escalations()
        
        # Find stale escalations (pending > 2 hours for critical, > 4 hours for high)
        now = datetime.utcnow()
        stale_critical = []
        stale_high = []
        
        for esc in pending:
            age = now - esc.created_at
            
            if esc.priority == EscalationPriority.CRITICAL and age > timedelta(hours=2):
                stale_critical.append(esc)
            elif esc.priority == EscalationPriority.HIGH and age > timedelta(hours=4):
                stale_high.append(esc)
        
        # Send reminders for stale escalations
        reminders_sent = 0
        
        for esc in stale_critical + stale_high:
            notify_escalation.delay(
                escalation_id=str(esc.escalation_id),
                priority=esc.priority.value,
                story_headline=f"[REMINDER] {esc.story_headline}",
                quality_score=esc.quality_score,
                concerns=["Awaiting review"] + esc.concerns[:3],
            )
            reminders_sent += 1
        
        logger.info(
            "escalation_queue_processed",
            total_pending=len(pending),
            stale_critical=len(stale_critical),
            stale_high=len(stale_high),
            reminders_sent=reminders_sent,
        )
        
        return {
            "pending": len(pending),
            "stale_critical": len(stale_critical),
            "stale_high": len(stale_high),
            "reminders_sent": reminders_sent,
        }
    
    return asyncio.run(_run())


@celery_app.task(name="undertow.escalation_stats_report")
def escalation_stats_report() -> dict[str, Any]:
    """
    Generate daily escalation statistics report.
    
    Returns:
        Statistics summary
    """
    import asyncio
    from datetime import datetime, timedelta
    
    async def _run() -> dict[str, Any]:
        from undertow.core.human_escalation import get_escalation_service
        
        service = get_escalation_service()
        
        # Get all escalations
        all_escalations = list(service._pending_escalations.values())
        
        # Calculate stats
        now = datetime.utcnow()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        today_created = sum(1 for e in all_escalations if e.created_at >= today)
        today_resolved = sum(1 for e in all_escalations if e.resolved_at and e.resolved_at >= today)
        
        # Resolution time for resolved escalations
        resolved = [e for e in all_escalations if e.resolved_at]
        if resolved:
            avg_resolution_hours = sum(
                (e.resolved_at - e.created_at).total_seconds() / 3600
                for e in resolved
            ) / len(resolved)
        else:
            avg_resolution_hours = 0
        
        stats = {
            "date": now.isoformat(),
            "total_pending": sum(1 for e in all_escalations if e.status.value == "pending"),
            "today_created": today_created,
            "today_resolved": today_resolved,
            "avg_resolution_hours": round(avg_resolution_hours, 1),
            "by_priority": {
                "critical": sum(1 for e in all_escalations if e.priority.value == "critical"),
                "high": sum(1 for e in all_escalations if e.priority.value == "high"),
                "medium": sum(1 for e in all_escalations if e.priority.value == "medium"),
                "low": sum(1 for e in all_escalations if e.priority.value == "low"),
            },
        }
        
        logger.info("escalation_stats_generated", **stats)
        
        return stats
    
    return asyncio.run(_run())

