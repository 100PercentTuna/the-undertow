"""
RSS/Atom feed fetcher.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import feedparser
import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger()


@dataclass
class FeedEntry:
    """A single entry from an RSS/Atom feed."""

    title: str
    link: str
    summary: str
    published: datetime | None
    author: str | None
    source_name: str
    raw_content: str | None = None
    categories: list[str] | None = None


class RSSFetcher:
    """
    Fetches and parses RSS/Atom feeds.
    
    Handles various feed formats and normalizes to FeedEntry.
    """

    def __init__(self, timeout: float = 30.0) -> None:
        """
        Initialize RSS fetcher.
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.client = httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": "The Undertow/1.0 (Geopolitical Intelligence)"},
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def fetch(self, feed_url: str) -> list[FeedEntry]:
        """
        Fetch and parse an RSS/Atom feed.
        
        Args:
            feed_url: URL of the feed
            
        Returns:
            List of FeedEntry objects
        """
        logger.debug("Fetching feed", url=feed_url)
        
        try:
            response = await self.client.get(feed_url)
            response.raise_for_status()
            
            # Parse feed
            feed = feedparser.parse(response.text)
            
            if feed.bozo and not feed.entries:
                logger.warning("Feed parse error", url=feed_url, error=str(feed.bozo_exception))
                return []
            
            # Extract source name from feed
            source_name = feed.feed.get("title", "Unknown Source")
            
            entries = []
            for entry in feed.entries:
                try:
                    parsed = self._parse_entry(entry, source_name)
                    entries.append(parsed)
                except Exception as e:
                    logger.warning(
                        "Failed to parse entry",
                        url=feed_url,
                        error=str(e),
                    )
            
            logger.info("Feed fetched", url=feed_url, entries=len(entries))
            return entries
            
        except httpx.HTTPError as e:
            logger.error("HTTP error fetching feed", url=feed_url, error=str(e))
            raise
        except Exception as e:
            logger.error("Error fetching feed", url=feed_url, error=str(e))
            raise

    def _parse_entry(self, entry: Any, source_name: str) -> FeedEntry:
        """Parse a single feed entry."""
        # Get title
        title = entry.get("title", "Untitled")
        
        # Get link
        link = entry.get("link", "")
        if not link and entry.get("links"):
            link = entry.links[0].get("href", "")
        
        # Get summary
        summary = ""
        if entry.get("summary"):
            summary = entry.summary
        elif entry.get("description"):
            summary = entry.description
        elif entry.get("content"):
            summary = entry.content[0].get("value", "")
        
        # Clean HTML from summary
        summary = self._strip_html(summary)
        
        # Get published date
        published = None
        if entry.get("published_parsed"):
            try:
                published = datetime(*entry.published_parsed[:6])
            except (TypeError, ValueError):
                pass
        elif entry.get("updated_parsed"):
            try:
                published = datetime(*entry.updated_parsed[:6])
            except (TypeError, ValueError):
                pass
        
        # Get author
        author = entry.get("author")
        
        # Get raw content if available
        raw_content = None
        if entry.get("content"):
            raw_content = entry.content[0].get("value", "")
        
        # Get categories/tags
        categories = None
        if entry.get("tags"):
            categories = [tag.get("term", "") for tag in entry.tags if tag.get("term")]
        
        return FeedEntry(
            title=title,
            link=link,
            summary=summary[:5000],  # Limit summary length
            published=published,
            author=author,
            source_name=source_name,
            raw_content=raw_content,
            categories=categories,
        )

    def _strip_html(self, text: str) -> str:
        """Remove HTML tags from text."""
        if not text:
            return ""
        
        # Simple HTML stripping - could use BeautifulSoup for robustness
        import re
        
        # Remove HTML tags
        text = re.sub(r"<[^>]+>", " ", text)
        # Normalize whitespace
        text = re.sub(r"\s+", " ", text)
        # Unescape HTML entities
        text = text.replace("&nbsp;", " ")
        text = text.replace("&amp;", "&")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&quot;", '"')
        
        return text.strip()

