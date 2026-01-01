"""
Source fetchers for different content types.
"""

from undertow.ingestion.fetchers.rss import RSSFetcher
from undertow.ingestion.fetchers.web import WebFetcher

__all__ = ["RSSFetcher", "WebFetcher"]

