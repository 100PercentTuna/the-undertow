"""
Web page content fetcher.
"""

from dataclasses import dataclass
from datetime import datetime

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger()


@dataclass
class WebContent:
    """Content extracted from a web page."""

    url: str
    title: str
    content: str
    author: str | None
    published: datetime | None
    word_count: int
    success: bool
    error: str | None = None


class WebFetcher:
    """
    Fetches and extracts content from web pages.
    
    Uses trafilatura for content extraction.
    """

    def __init__(self, timeout: float = 30.0) -> None:
        """
        Initialize web fetcher.
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.client = httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; The Undertow/1.0)",
                "Accept": "text/html,application/xhtml+xml",
            },
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def fetch(self, url: str) -> WebContent:
        """
        Fetch and extract content from a URL.
        
        Args:
            url: URL to fetch
            
        Returns:
            WebContent with extracted text
        """
        logger.debug("Fetching web page", url=url)
        
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            
            html = response.text
            
            # Extract content using trafilatura
            try:
                import trafilatura
                
                extracted = trafilatura.extract(
                    html,
                    include_comments=False,
                    include_tables=True,
                    no_fallback=False,
                    favor_precision=True,
                )
                
                if not extracted:
                    return WebContent(
                        url=url,
                        title="",
                        content="",
                        author=None,
                        published=None,
                        word_count=0,
                        success=False,
                        error="Could not extract content",
                    )
                
                # Get metadata
                metadata = trafilatura.extract_metadata(html)
                
                title = metadata.title if metadata else ""
                author = metadata.author if metadata else None
                published = None
                if metadata and metadata.date:
                    try:
                        from dateutil import parser
                        published = parser.parse(metadata.date)
                    except Exception:
                        pass
                
                word_count = len(extracted.split())
                
                logger.info(
                    "Web page fetched",
                    url=url,
                    word_count=word_count,
                )
                
                return WebContent(
                    url=url,
                    title=title,
                    content=extracted,
                    author=author,
                    published=published,
                    word_count=word_count,
                    success=True,
                )
                
            except ImportError:
                logger.warning("trafilatura not available, using basic extraction")
                return self._basic_extract(url, html)
            
        except httpx.HTTPError as e:
            logger.error("HTTP error fetching page", url=url, error=str(e))
            return WebContent(
                url=url,
                title="",
                content="",
                author=None,
                published=None,
                word_count=0,
                success=False,
                error=str(e),
            )
        except Exception as e:
            logger.error("Error fetching page", url=url, error=str(e))
            return WebContent(
                url=url,
                title="",
                content="",
                author=None,
                published=None,
                word_count=0,
                success=False,
                error=str(e),
            )

    def _basic_extract(self, url: str, html: str) -> WebContent:
        """Basic content extraction fallback using BeautifulSoup."""
        try:
            from bs4 import BeautifulSoup
            
            soup = BeautifulSoup(html, "html.parser")
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Get title
            title = ""
            if soup.title:
                title = soup.title.string or ""
            
            # Get text
            text = soup.get_text(separator=" ", strip=True)
            
            # Clean up whitespace
            import re
            text = re.sub(r"\s+", " ", text)
            
            word_count = len(text.split())
            
            return WebContent(
                url=url,
                title=title,
                content=text[:50000],  # Limit content length
                author=None,
                published=None,
                word_count=word_count,
                success=True,
            )
            
        except ImportError:
            logger.error("BeautifulSoup not available")
            return WebContent(
                url=url,
                title="",
                content="",
                author=None,
                published=None,
                word_count=0,
                success=False,
                error="No extraction library available",
            )

