"""
Notification service for The Undertow.

Handles email, Slack, and webhook notifications.
"""

import structlog
from dataclasses import dataclass
from enum import Enum
from typing import Any
import httpx

from undertow.config import get_settings

logger = structlog.get_logger(__name__)


class NotificationChannel(str, Enum):
    """Notification channels."""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"


class NotificationPriority(str, Enum):
    """Notification priority levels."""
    URGENT = "urgent"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


@dataclass
class Notification:
    """Notification model."""
    channel: NotificationChannel
    priority: NotificationPriority
    subject: str
    body: str
    metadata: dict[str, Any] | None = None


class NotificationService:
    """
    Service for sending notifications across channels.
    
    Supports email (SendGrid), Slack webhooks, and custom webhooks.
    """
    
    def __init__(self) -> None:
        self._settings = get_settings()
    
    async def send(self, notification: Notification) -> bool:
        """
        Send a notification.
        
        Args:
            notification: Notification to send
            
        Returns:
            True if sent successfully
        """
        try:
            if notification.channel == NotificationChannel.EMAIL:
                return await self._send_email(notification)
            elif notification.channel == NotificationChannel.SLACK:
                return await self._send_slack(notification)
            elif notification.channel == NotificationChannel.WEBHOOK:
                return await self._send_webhook(notification)
            else:
                logger.warning("unknown_notification_channel", channel=notification.channel)
                return False
        except Exception as e:
            logger.error(
                "notification_failed",
                channel=notification.channel,
                error=str(e),
            )
            return False
    
    async def send_multi(
        self,
        channels: list[NotificationChannel],
        subject: str,
        body: str,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, bool]:
        """
        Send notification to multiple channels.
        
        Args:
            channels: List of channels to notify
            subject: Notification subject
            body: Notification body
            priority: Priority level
            metadata: Additional metadata
            
        Returns:
            Dict of channel -> success status
        """
        results = {}
        
        for channel in channels:
            notification = Notification(
                channel=channel,
                priority=priority,
                subject=subject,
                body=body,
                metadata=metadata,
            )
            results[channel.value] = await self.send(notification)
        
        return results
    
    async def _send_email(self, notification: Notification) -> bool:
        """Send email via SendGrid."""
        if not self._settings.sendgrid_api_key:
            logger.warning("sendgrid_not_configured")
            return False
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers={
                    "Authorization": f"Bearer {self._settings.sendgrid_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "personalizations": [
                        {"to": [{"email": self._settings.alert_email}]}
                    ],
                    "from": {
                        "email": self._settings.from_email,
                        "name": "The Undertow",
                    },
                    "subject": notification.subject,
                    "content": [
                        {"type": "text/plain", "value": notification.body}
                    ],
                },
            )
            
            if response.status_code >= 400:
                logger.error(
                    "sendgrid_error",
                    status=response.status_code,
                    body=response.text,
                )
                return False
            
            logger.info("email_sent", subject=notification.subject)
            return True
    
    async def _send_slack(self, notification: Notification) -> bool:
        """Send Slack webhook notification."""
        webhook_url = self._settings.slack_webhook_url
        
        if not webhook_url:
            logger.warning("slack_webhook_not_configured")
            return False
        
        # Format for Slack
        priority_emoji = {
            NotificationPriority.URGENT: "🚨",
            NotificationPriority.HIGH: "⚠️",
            NotificationPriority.NORMAL: "📋",
            NotificationPriority.LOW: "📝",
        }.get(notification.priority, "📋")
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{priority_emoji} {notification.subject}",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": notification.body,
                },
            },
        ]
        
        # Add metadata fields if present
        if notification.metadata:
            fields = [
                {
                    "type": "mrkdwn",
                    "text": f"*{k}:*\n{v}",
                }
                for k, v in list(notification.metadata.items())[:10]
            ]
            blocks.append({
                "type": "section",
                "fields": fields,
            })
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                webhook_url,
                json={"blocks": blocks},
            )
            
            if response.status_code >= 400:
                logger.error(
                    "slack_error",
                    status=response.status_code,
                )
                return False
            
            logger.info("slack_sent", subject=notification.subject)
            return True
    
    async def _send_webhook(self, notification: Notification) -> bool:
        """Send generic webhook notification."""
        from undertow.services.webhooks import WebhookService
        
        webhook_service = WebhookService()
        
        await webhook_service.send(
            event_type="notification",
            payload={
                "subject": notification.subject,
                "body": notification.body,
                "priority": notification.priority.value,
                "metadata": notification.metadata or {},
            },
        )
        
        return True


# Singleton instance
_notification_service: NotificationService | None = None


def get_notification_service() -> NotificationService:
    """Get or create notification service instance."""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service


# Convenience functions
async def notify_escalation_created(
    escalation_id: str,
    story_headline: str,
    priority: str,
    quality_score: float,
    concerns: list[str],
) -> None:
    """Send notification for new escalation."""
    service = get_notification_service()
    
    priority_map = {
        "critical": NotificationPriority.URGENT,
        "high": NotificationPriority.HIGH,
        "medium": NotificationPriority.NORMAL,
        "low": NotificationPriority.LOW,
    }
    
    # Determine channels based on priority
    channels = [NotificationChannel.WEBHOOK]
    if priority in ("critical", "high"):
        channels.append(NotificationChannel.EMAIL)
        channels.append(NotificationChannel.SLACK)
    
    await service.send_multi(
        channels=channels,
        subject=f"[{priority.upper()}] Escalation: {story_headline[:50]}...",
        body=f"""
A new escalation requires human review.

Story: {story_headline}
Quality Score: {quality_score:.0%}

Concerns:
{chr(10).join(f'• {c}' for c in concerns[:5])}
        """.strip(),
        priority=priority_map.get(priority, NotificationPriority.NORMAL),
        metadata={
            "escalation_id": escalation_id,
            "quality_score": f"{quality_score:.0%}",
        },
    )


async def notify_pipeline_complete(
    run_id: str,
    articles_generated: int,
    quality_avg: float,
    duration_seconds: float,
    total_cost: float,
) -> None:
    """Send notification for pipeline completion."""
    service = get_notification_service()
    
    await service.send_multi(
        channels=[NotificationChannel.WEBHOOK, NotificationChannel.SLACK],
        subject=f"Pipeline Complete: {articles_generated} articles",
        body=f"""
Daily pipeline run completed successfully.

Articles: {articles_generated}
Average Quality: {quality_avg:.0%}
Duration: {duration_seconds/60:.1f} minutes
Cost: ${total_cost:.2f}
        """.strip(),
        priority=NotificationPriority.NORMAL,
        metadata={
            "run_id": run_id,
            "articles": str(articles_generated),
            "quality": f"{quality_avg:.0%}",
            "cost": f"${total_cost:.2f}",
        },
    )


async def notify_pipeline_failed(
    run_id: str,
    error: str,
    stage: str,
) -> None:
    """Send notification for pipeline failure."""
    service = get_notification_service()
    
    await service.send_multi(
        channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK, NotificationChannel.WEBHOOK],
        subject=f"🚨 Pipeline Failed at {stage}",
        body=f"""
Pipeline run failed and requires attention.

Run ID: {run_id}
Stage: {stage}
Error: {error}
        """.strip(),
        priority=NotificationPriority.URGENT,
        metadata={
            "run_id": run_id,
            "stage": stage,
            "error": error[:200],
        },
    )

