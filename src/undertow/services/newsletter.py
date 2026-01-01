"""
Newsletter service for email delivery.

Handles:
- Newsletter compilation
- Email rendering
- Delivery via SendGrid
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import structlog

from undertow.config import settings

logger = structlog.get_logger()


@dataclass
class NewsletterArticle:
    """Article formatted for newsletter."""

    headline: str
    subhead: str
    summary: str
    content: str
    read_time: int
    zones: list[str]
    url: str | None = None


@dataclass
class Newsletter:
    """Complete newsletter edition."""

    edition_date: datetime
    edition_number: int
    preamble: str
    articles: list[NewsletterArticle]
    closing: str


class NewsletterService:
    """
    Service for compiling and sending newsletters.

    Example:
        service = NewsletterService()
        newsletter = await service.compile_edition(articles)
        await service.send_to_subscribers(newsletter, subscribers)
    """

    def __init__(self) -> None:
        """Initialize newsletter service."""
        self.from_email = settings.from_email
        self.sendgrid_key = settings.sendgrid_api_key

    async def compile_edition(
        self,
        articles: list[dict[str, Any]],
        edition_date: datetime | None = None,
        edition_number: int = 0,
        preamble: str = "",
    ) -> Newsletter:
        """
        Compile newsletter from articles.

        Args:
            articles: List of article dicts
            edition_date: Edition date
            edition_number: Edition number
            preamble: Opening text

        Returns:
            Compiled Newsletter
        """
        edition_date = edition_date or datetime.utcnow()

        # Convert articles to newsletter format
        newsletter_articles = [
            NewsletterArticle(
                headline=a.get("headline", ""),
                subhead=a.get("subhead", ""),
                summary=a.get("summary", ""),
                content=self._format_content(a.get("content", "")),
                read_time=a.get("read_time_minutes", 5),
                zones=a.get("zones", []),
                url=a.get("url"),
            )
            for a in articles
        ]

        # Generate closing
        closing = self._generate_closing(edition_date)

        return Newsletter(
            edition_date=edition_date,
            edition_number=edition_number,
            preamble=preamble or self._generate_preamble(edition_date),
            articles=newsletter_articles,
            closing=closing,
        )

    def render_html(self, newsletter: Newsletter) -> str:
        """
        Render newsletter as HTML email.

        Args:
            newsletter: Newsletter to render

        Returns:
            HTML string
        """
        articles_html = "\n".join(
            self._render_article_html(a) for a in newsletter.articles
        )

        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>The Undertow - {newsletter.edition_date.strftime('%B %d, %Y')}</title>
    <style>
        body {{
            font-family: 'Georgia', serif;
            line-height: 1.6;
            color: #1a1a1a;
            max-width: 680px;
            margin: 0 auto;
            padding: 20px;
            background-color: #fafafa;
        }}
        .header {{
            border-bottom: 3px solid #1a1a1a;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .logo {{
            font-size: 32px;
            font-weight: bold;
            letter-spacing: -1px;
            color: #1a1a1a;
        }}
        .tagline {{
            font-style: italic;
            color: #666;
            margin-top: 5px;
        }}
        .edition-info {{
            color: #666;
            font-size: 14px;
            margin-top: 10px;
        }}
        .preamble {{
            background-color: #f0f0f0;
            padding: 20px;
            border-left: 4px solid #1a1a1a;
            margin-bottom: 40px;
        }}
        .article {{
            margin-bottom: 50px;
            padding-bottom: 30px;
            border-bottom: 1px solid #ddd;
        }}
        .article:last-child {{
            border-bottom: none;
        }}
        .article-headline {{
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 5px;
            color: #1a1a1a;
        }}
        .article-subhead {{
            font-size: 16px;
            color: #666;
            margin-bottom: 15px;
        }}
        .article-meta {{
            font-size: 12px;
            color: #888;
            margin-bottom: 15px;
        }}
        .article-content {{
            font-size: 16px;
        }}
        .closing {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 3px solid #1a1a1a;
            font-style: italic;
        }}
        a {{
            color: #0066cc;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">THE UNDERTOW</div>
        <div class="tagline">Intelligence for serious people</div>
        <div class="edition-info">
            {newsletter.edition_date.strftime('%A, %B %d, %Y')}
            {f' • Edition #{newsletter.edition_number}' if newsletter.edition_number else ''}
        </div>
    </div>
    
    <div class="preamble">
        {newsletter.preamble}
    </div>
    
    {articles_html}
    
    <div class="closing">
        {newsletter.closing}
    </div>
</body>
</html>"""

    def render_text(self, newsletter: Newsletter) -> str:
        """
        Render newsletter as plain text.

        Args:
            newsletter: Newsletter to render

        Returns:
            Plain text string
        """
        articles_text = "\n\n".join(
            self._render_article_text(a) for a in newsletter.articles
        )

        return f"""THE UNDERTOW
Intelligence for serious people

{newsletter.edition_date.strftime('%A, %B %d, %Y')}
{'Edition #' + str(newsletter.edition_number) if newsletter.edition_number else ''}

{'=' * 60}

{newsletter.preamble}

{'=' * 60}

{articles_text}

{'=' * 60}

{newsletter.closing}

---
The Undertow
Unsubscribe: [unsubscribe_link]
"""

    async def send_to_subscribers(
        self,
        newsletter: Newsletter,
        subscribers: list[str],
    ) -> dict[str, Any]:
        """
        Send newsletter to subscribers.

        Args:
            newsletter: Newsletter to send
            subscribers: List of email addresses

        Returns:
            Send result
        """
        if not self.sendgrid_key:
            logger.warning("SendGrid not configured, skipping send")
            return {"status": "skipped", "reason": "no_api_key"}

        try:
            import sendgrid
            from sendgrid.helpers.mail import Mail, Email, To, Content

            sg = sendgrid.SendGridAPIClient(api_key=self.sendgrid_key)

            html_content = self.render_html(newsletter)
            text_content = self.render_text(newsletter)

            subject = (
                f"The Undertow - {newsletter.edition_date.strftime('%B %d, %Y')}"
            )

            sent = 0
            failed = 0
            errors = []

            for subscriber in subscribers:
                try:
                    message = Mail(
                        from_email=Email(self.from_email, "The Undertow"),
                        to_emails=To(subscriber),
                        subject=subject,
                    )
                    message.add_content(Content("text/plain", text_content))
                    message.add_content(Content("text/html", html_content))

                    response = sg.send(message)

                    if response.status_code in [200, 201, 202]:
                        sent += 1
                    else:
                        failed += 1
                        errors.append({
                            "email": subscriber,
                            "status": response.status_code,
                        })

                except Exception as e:
                    failed += 1
                    errors.append({"email": subscriber, "error": str(e)})

            logger.info(
                "Newsletter sent",
                sent=sent,
                failed=failed,
                total=len(subscribers),
            )

            return {
                "status": "completed",
                "sent": sent,
                "failed": failed,
                "errors": errors[:10],  # Limit error details
            }

        except ImportError:
            logger.error("SendGrid package not installed")
            return {"status": "error", "reason": "sendgrid_not_installed"}

        except Exception as e:
            logger.error("Failed to send newsletter", error=str(e))
            return {"status": "error", "reason": str(e)}

    def _render_article_html(self, article: NewsletterArticle) -> str:
        """Render single article as HTML."""
        return f"""
    <div class="article">
        <div class="article-headline">{article.headline}</div>
        <div class="article-subhead">{article.subhead}</div>
        <div class="article-meta">
            {' • '.join(article.zones)} • {article.read_time} min read
        </div>
        <div class="article-content">
            {article.content[:2000]}...
            {'<p><a href="' + article.url + '">Read full article →</a></p>' if article.url else ''}
        </div>
    </div>"""

    def _render_article_text(self, article: NewsletterArticle) -> str:
        """Render single article as text."""
        return f"""{article.headline.upper()}
{article.subhead}

{' • '.join(article.zones)} • {article.read_time} min read

{article.content[:1500]}...
{f'Read full article: {article.url}' if article.url else ''}
"""

    def _format_content(self, content: str) -> str:
        """Format content for newsletter."""
        # Basic formatting - could be enhanced
        return content.replace("\n\n", "</p><p>").replace("\n", "<br>")

    def _generate_preamble(self, date: datetime) -> str:
        """Generate default preamble."""
        day_name = date.strftime("%A")
        return (
            f"Good morning. It's {day_name}, and here's what matters in the "
            f"world today. As always, we're looking beyond the headlines to "
            f"trace the chains of consequence and motivation that reveal "
            f"what game is actually being played."
        )

    def _generate_closing(self, date: datetime) -> str:
        """Generate closing text."""
        return (
            "That's all for today. The world will keep turning, power will "
            "keep shifting, and we'll be here tomorrow tracing the chains. "
            "If something in today's edition sparked a thought, we'd love to "
            "hear it. Until then, watch what they do, not what they say."
        )

