"""
Webhook notification service.

Sends notifications when events occur (article published, pipeline complete, etc.).
"""

import asyncio
import hashlib
import hmac
import json
from datetime import datetime
from enum import Enum
from typing import Any

import httpx
import structlog

from undertow.config import settings

logger = structlog.get_logger()


class WebhookEvent(str, Enum):
    """Webhook event types."""

    PIPELINE_STARTED = "pipeline.started"
    PIPELINE_COMPLETED = "pipeline.completed"
    PIPELINE_FAILED = "pipeline.failed"

    STORY_CREATED = "story.created"
    STORY_ANALYZED = "story.analyzed"

    ARTICLE_DRAFTED = "article.drafted"
    ARTICLE_APPROVED = "article.approved"
    ARTICLE_PUBLISHED = "article.published"

    NEWSLETTER_SENT = "newsletter.sent"

    QUALITY_GATE_FAILED = "quality.gate_failed"
    BUDGET_WARNING = "budget.warning"
    BUDGET_EXCEEDED = "budget.exceeded"


class WebhookService:
    """
    Service for sending webhook notifications.

    Example:
        service = WebhookService()
        await service.send(
            event=WebhookEvent.ARTICLE_PUBLISHED,
            payload={"article_id": "123", "headline": "..."},
        )
    """

    def __init__(
        self,
        webhook_urls: list[str] | None = None,
        secret: str | None = None,
        timeout: float = 10.0,
    ) -> None:
        """
        Initialize webhook service.

        Args:
            webhook_urls: List of webhook URLs to notify
            secret: Secret for signing payloads
            timeout: Request timeout in seconds
        """
        self.webhook_urls = webhook_urls or []
        self.secret = secret or settings.secret_key
        self.timeout = timeout

    async def send(
        self,
        event: WebhookEvent,
        payload: dict[str, Any],
        urls: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Send webhook to all configured URLs.

        Args:
            event: Event type
            payload: Event payload
            urls: Override URLs (uses configured if not provided)

        Returns:
            Results dict with successes and failures
        """
        target_urls = urls or self.webhook_urls

        if not target_urls:
            logger.debug("No webhook URLs configured")
            return {"sent": 0, "failed": 0, "skipped": True}

        # Build full payload
        full_payload = {
            "event": event.value,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "payload": payload,
        }

        # Compute signature
        signature = self._compute_signature(full_payload)

        # Send to all URLs concurrently
        tasks = [
            self._send_to_url(url, full_payload, signature)
            for url in target_urls
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Count results
        successes = sum(1 for r in results if r is True)
        failures = len(results) - successes

        logger.info(
            "Webhooks sent",
            event=event.value,
            sent=successes,
            failed=failures,
        )

        return {
            "sent": successes,
            "failed": failures,
            "total_urls": len(target_urls),
        }

    async def _send_to_url(
        self,
        url: str,
        payload: dict[str, Any],
        signature: str,
    ) -> bool:
        """
        Send webhook to a single URL.

        Args:
            url: Target URL
            payload: Payload to send
            signature: HMAC signature

        Returns:
            True if successful
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "X-Webhook-Signature": signature,
                        "X-Webhook-Event": payload["event"],
                        "User-Agent": "TheUndertow/1.0",
                    },
                )

                if response.status_code < 300:
                    logger.debug("Webhook delivered", url=url[:50])
                    return True
                else:
                    logger.warning(
                        "Webhook failed",
                        url=url[:50],
                        status=response.status_code,
                    )
                    return False

        except Exception as e:
            logger.error("Webhook error", url=url[:50], error=str(e))
            return False

    def _compute_signature(self, payload: dict[str, Any]) -> str:
        """
        Compute HMAC signature for payload.

        Args:
            payload: Payload to sign

        Returns:
            Hex-encoded signature
        """
        payload_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
        signature = hmac.new(
            self.secret.encode("utf-8"),
            payload_bytes,
            hashlib.sha256,
        ).hexdigest()
        return f"sha256={signature}"

    @staticmethod
    def verify_signature(
        payload: dict[str, Any],
        signature: str,
        secret: str,
    ) -> bool:
        """
        Verify webhook signature (for receiving webhooks).

        Args:
            payload: Received payload
            signature: Received signature header
            secret: Expected secret

        Returns:
            True if signature is valid
        """
        if not signature.startswith("sha256="):
            return False

        expected_sig = signature[7:]  # Remove "sha256=" prefix
        payload_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
        computed = hmac.new(
            secret.encode("utf-8"),
            payload_bytes,
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(expected_sig, computed)


# Convenience functions
_webhook_service: WebhookService | None = None


def get_webhook_service() -> WebhookService:
    """Get global webhook service instance."""
    global _webhook_service
    if _webhook_service is None:
        _webhook_service = WebhookService()
    return _webhook_service


async def send_webhook(
    event: WebhookEvent,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """
    Send webhook notification.

    Convenience function using global service.
    """
    service = get_webhook_service()
    return await service.send(event, payload)

