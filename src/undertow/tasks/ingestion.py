"""
Ingestion tasks for fetching from sources.
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog
import yaml

from undertow.config import settings
from undertow.infrastructure.database import init_db, get_session
from undertow.repositories import StoryRepository
from undertow.models.story import Story, StoryStatus, Zone

logger = structlog.get_logger()


def ingest_all_sources() -> dict[str, Any]:
    """
    Ingest from all configured sources.

    Synchronous wrapper for async implementation.
    """
    return asyncio.run(_ingest_all_sources_async())


async def _ingest_all_sources_async() -> dict[str, Any]:
    """Async implementation of source ingestion."""
    logger.info("Starting source ingestion")

    # Load feed config
    config_path = Path("config/feeds.yaml")
    if not config_path.exists():
        logger.warning("No feeds.yaml found")
        return {"feeds_processed": 0, "stories_fetched": 0, "stories_added": 0}

    with open(config_path) as f:
        config = yaml.safe_load(f)

    await init_db()

    feeds_processed = 0
    stories_fetched = 0
    stories_added = 0
    errors: list[dict[str, Any]] = []

    async for session in get_session():
        story_repo = StoryRepository(session)

        # Process zone feeds
        zones = config.get("zones", {})
        for zone_id, zone_config in zones.items():
            feeds = zone_config.get("feeds", [])
            for feed in feeds:
                try:
                    result = await _process_feed(
                        feed=feed,
                        zone_id=zone_id,
                        story_repo=story_repo,
                    )
                    feeds_processed += 1
                    stories_fetched += result["fetched"]
                    stories_added += result["added"]

                except Exception as e:
                    logger.error(
                        "Failed to process feed",
                        feed=feed.get("name"),
                        error=str(e),
                    )
                    errors.append({
                        "feed": feed.get("name"),
                        "error": str(e),
                    })

        # Process global sources
        global_sources = config.get("global_sources", [])
        for feed in global_sources:
            try:
                result = await _process_feed(
                    feed=feed,
                    zone_id=None,
                    story_repo=story_repo,
                )
                feeds_processed += 1
                stories_fetched += result["fetched"]
                stories_added += result["added"]

            except Exception as e:
                logger.error(
                    "Failed to process global feed",
                    feed=feed.get("name"),
                    error=str(e),
                )
                errors.append({
                    "feed": feed.get("name"),
                    "error": str(e),
                })

        await session.commit()

    result = {
        "feeds_processed": feeds_processed,
        "stories_fetched": stories_fetched,
        "stories_added": stories_added,
        "errors": errors[:10],  # Limit errors
    }

    logger.info("Ingestion completed", **result)
    return result


async def _process_feed(
    feed: dict[str, Any],
    zone_id: str | None,
    story_repo: StoryRepository,
) -> dict[str, int]:
    """Process a single RSS feed."""
    import feedparser

    url = feed.get("url")
    if not url:
        return {"fetched": 0, "added": 0}

    logger.info(f"Processing feed: {feed.get('name')}")

    # Fetch feed (runs in executor to not block)
    loop = asyncio.get_event_loop()
    parsed = await loop.run_in_executor(None, feedparser.parse, url)

    if parsed.bozo:
        logger.warning(f"Feed parsing issue: {feed.get('name')}")

    fetched = 0
    added = 0

    for entry in parsed.entries[:20]:  # Limit entries per feed
        fetched += 1

        # Check if already exists
        entry_url = entry.get("link", "")
        if entry_url:
            existing = await story_repo.get_by_url(entry_url)
            if existing:
                continue

        # Create story
        try:
            # Determine zone enum
            zone_enum = None
            if zone_id:
                try:
                    zone_enum = Zone(zone_id)
                except ValueError:
                    pass

            story = Story(
                headline=entry.get("title", "Untitled")[:500],
                summary=_clean_summary(entry.get("summary", ""))[:2000],
                source_url=entry_url,
                source_name=feed.get("name", "Unknown"),
                primary_zone=zone_enum,
                status=StoryStatus.PENDING,
                relevance_score=_estimate_relevance(entry, feed.get("priority", 3)),
            )

            await story_repo.create(story)
            added += 1

        except Exception as e:
            logger.warning(
                "Failed to create story",
                url=entry_url[:100],
                error=str(e),
            )

    return {"fetched": fetched, "added": added}


def _clean_summary(text: str) -> str:
    """Clean HTML from summary."""
    import re

    # Remove HTML tags
    clean = re.sub(r"<[^>]+>", "", text)
    # Collapse whitespace
    clean = re.sub(r"\s+", " ", clean)
    return clean.strip()


def _estimate_relevance(entry: dict, priority: int) -> float:
    """Estimate relevance score from entry metadata."""
    # Base score from feed priority (1-5, where 1 is highest)
    base = 1.0 - (priority - 1) * 0.15

    # Boost for longer content
    content_len = len(entry.get("summary", ""))
    if content_len > 500:
        base += 0.1
    elif content_len > 200:
        base += 0.05

    # Cap at 1.0
    return min(1.0, max(0.0, base))
