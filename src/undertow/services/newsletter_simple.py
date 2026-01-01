"""
Simple newsletter service for The Undertow.

Sends daily newsletter via SendGrid.
"""

import structlog
from datetime import datetime
from typing import Any

import httpx

from undertow.config import get_settings
from undertow.schemas.articles import Article

logger = structlog.get_logger(__name__)


class NewsletterService:
    """
    Simple newsletter service.
    
    Sends HTML emails via SendGrid.
    """
    
    def __init__(self) -> None:
        self._settings = get_settings()
    
    async def send_daily_newsletter(
        self,
        articles: list[Article],
        recipients: list[str],
    ) -> bool:
        """
        Send the daily newsletter.
        
        Args:
            articles: List of articles to include
            recipients: List of email addresses
            
        Returns:
            True if sent successfully
        """
        if not recipients:
            logger.warning("no_recipients_configured")
            return False
        
        if not self._settings.sendgrid_api_key:
            logger.error("sendgrid_not_configured")
            return False
        
        # Build newsletter HTML
        html = self._build_html(articles)
        text = self._build_text(articles)
        
        # Send to each recipient
        success_count = 0
        for recipient in recipients:
            try:
                await self._send_email(
                    to_email=recipient,
                    subject=self._get_subject(),
                    html_content=html,
                    text_content=text,
                )
                success_count += 1
            except Exception as e:
                logger.error("email_send_failed", recipient=recipient, error=str(e))
        
        logger.info(
            "newsletter_sent",
            recipients=len(recipients),
            success=success_count,
            articles=len(articles),
        )
        
        return success_count > 0
    
    async def _send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str,
    ) -> None:
        """Send a single email via SendGrid."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers={
                    "Authorization": f"Bearer {self._settings.sendgrid_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "personalizations": [{"to": [{"email": to_email}]}],
                    "from": {
                        "email": self._settings.from_email,
                        "name": "The Undertow",
                    },
                    "subject": subject,
                    "content": [
                        {"type": "text/plain", "value": text_content},
                        {"type": "text/html", "value": html_content},
                    ],
                },
            )
            
            if response.status_code >= 400:
                raise Exception(f"SendGrid error: {response.status_code}")
    
    def _get_subject(self) -> str:
        """Generate email subject."""
        today = datetime.utcnow().strftime("%B %d, %Y")
        return f"The Undertow — {today}"
    
    def _build_html(self, articles: list[Article]) -> str:
        """Build HTML newsletter."""
        today = datetime.utcnow().strftime("%B %d, %Y")
        
        articles_html = ""
        for i, article in enumerate(articles, 1):
            zones_str = " · ".join(z.upper().replace("_", " ") for z in article.zones[:2])
            articles_html += f"""
            <div style="margin-bottom: 40px; padding-bottom: 40px; border-bottom: 1px solid #334155;">
                <div style="color: #64748b; font-size: 12px; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 0.05em;">
                    {zones_str}
                </div>
                <h2 style="font-size: 22px; color: #f1f5f9; margin: 0 0 15px; line-height: 1.3;">
                    {article.headline}
                </h2>
                <div style="color: #cbd5e1; font-size: 16px; line-height: 1.7;">
                    {self._format_content(article.content)}
                </div>
            </div>
            """
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; background-color: #0f172a; font-family: Georgia, serif;">
    <div style="max-width: 680px; margin: 0 auto; padding: 40px 20px;">
        
        <!-- Header -->
        <div style="text-align: center; margin-bottom: 50px; padding-bottom: 30px; border-bottom: 2px solid #f59e0b;">
            <h1 style="color: #f59e0b; font-size: 32px; margin: 0; font-family: -apple-system, BlinkMacSystemFont, sans-serif; letter-spacing: 0.1em;">
                THE UNDERTOW
            </h1>
            <p style="color: #64748b; margin: 10px 0 0; font-size: 14px;">
                Intelligence for Serious People · {today}
            </p>
        </div>
        
        <!-- Articles -->
        {articles_html}
        
        <!-- Footer -->
        <div style="text-align: center; padding-top: 30px; color: #64748b; font-size: 12px;">
            <p style="margin: 0;">
                The Undertow — Tracing the chains far enough to see what game is really being played.
            </p>
            <p style="margin: 15px 0 0;">
                <a href="#" style="color: #f59e0b; text-decoration: none;">Unsubscribe</a>
            </p>
        </div>
        
    </div>
</body>
</html>
"""
    
    def _build_text(self, articles: list[Article]) -> str:
        """Build plain text newsletter."""
        today = datetime.utcnow().strftime("%B %d, %Y")
        
        text = f"THE UNDERTOW\n"
        text += f"Intelligence for Serious People · {today}\n"
        text += "=" * 60 + "\n\n"
        
        for article in articles:
            zones_str = " · ".join(z.upper().replace("_", " ") for z in article.zones[:2])
            text += f"{zones_str}\n"
            text += f"{article.headline}\n"
            text += "-" * 40 + "\n"
            text += f"{article.content}\n\n"
            text += "=" * 60 + "\n\n"
        
        text += "The Undertow — Tracing the chains far enough to see what game is really being played.\n"
        
        return text
    
    def _format_content(self, content: str) -> str:
        """Format article content for HTML."""
        # Split into paragraphs
        paragraphs = content.split("\n\n")
        
        html = ""
        for p in paragraphs:
            p = p.strip()
            if not p:
                continue
            
            # Check for headers
            if p.startswith("## "):
                html += f'<h3 style="color: #94a3b8; font-size: 14px; margin: 30px 0 15px; text-transform: uppercase; letter-spacing: 0.05em; font-family: -apple-system, BlinkMacSystemFont, sans-serif;">{p[3:]}</h3>'
            elif p.startswith("### "):
                html += f'<h4 style="color: #cbd5e1; font-size: 16px; margin: 20px 0 10px; font-family: -apple-system, BlinkMacSystemFont, sans-serif;">{p[4:]}</h4>'
            else:
                html += f'<p style="margin: 0 0 15px;">{p}</p>'
        
        return html

