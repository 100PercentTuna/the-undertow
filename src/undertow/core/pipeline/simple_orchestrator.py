"""
Simplified pipeline orchestrator for The Undertow.

Optimized for ~$1/day operation:
- Uses cheap models (Claude Haiku, GPT-4o-mini)
- No caching layer
- No human review
- Streamlined analysis
"""

import asyncio
import structlog
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

from undertow.config import get_settings
from undertow.llm.router import get_router
from undertow.schemas.stories import Story
from undertow.schemas.articles import Article

logger = structlog.get_logger(__name__)


@dataclass
class PipelineResult:
    """Result of a pipeline run."""
    
    success: bool
    articles: list[Article] = field(default_factory=list)
    total_cost: float = 0.0
    duration_seconds: float = 0.0
    error: str | None = None


@dataclass
class ArticleOutput:
    """Generated article output."""
    
    headline: str
    content: str
    summary: str
    zones: list[str]
    quality_score: float
    cost: float


class SimpleOrchestrator:
    """
    Simplified pipeline orchestrator.
    
    Optimized for low cost (~$1/day):
    - 5 articles per day
    - Uses Claude Haiku for most tasks ($0.25/1M input, $1.25/1M output)
    - Single-pass analysis (no multi-round debates)
    - Auto-publishes without human review
    
    Cost breakdown per article:
    - Story selection: ~$0.01
    - Analysis: ~$0.05
    - Writing: ~$0.10
    - Editing: ~$0.02
    - Total: ~$0.18/article × 5 = ~$0.90/day
    """
    
    def __init__(self) -> None:
        self._settings = get_settings()
        self._router = get_router()
        self._total_cost = 0.0
    
    async def run_daily(self) -> PipelineResult:
        """
        Run the daily pipeline.
        
        Returns 5 articles ready for newsletter.
        """
        start_time = datetime.utcnow()
        self._total_cost = 0.0
        
        try:
            # Step 1: Select today's stories
            stories = await self._select_stories()
            logger.info("stories_selected", count=len(stories))
            
            # Step 2: Generate articles for each story
            articles = []
            for story in stories[:5]:  # Limit to 5
                article = await self._generate_article(story)
                if article:
                    articles.append(article)
                    logger.info(
                        "article_generated",
                        headline=article.headline[:50],
                        cost=article.cost,
                    )
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            return PipelineResult(
                success=True,
                articles=[self._to_article(a) for a in articles],
                total_cost=self._total_cost,
                duration_seconds=duration,
            )
        
        except Exception as e:
            logger.exception("pipeline_failed", error=str(e))
            return PipelineResult(
                success=False,
                error=str(e),
                total_cost=self._total_cost,
            )
    
    async def _select_stories(self) -> list[Story]:
        """
        Select stories for today's analysis.
        
        Uses Claude Haiku to identify 5 significant stories.
        """
        # In production, this would:
        # 1. Fetch recent news from RSS feeds
        # 2. Use LLM to rank by significance
        # For now, return placeholder stories
        
        prompt = """You are a geopolitical analyst. Based on today's news, identify 5 significant 
stories that warrant deep analysis. Focus on:
- Events with non-obvious second/third order consequences
- Situations where the public narrative may miss the real story
- Developments that connect multiple regions/actors

For each story, provide:
1. Headline
2. Brief summary (2-3 sentences)
3. Primary zone (from our 42-zone system)
4. Why it matters

Format as JSON array."""

        response = await self._router.complete(
            prompt=prompt,
            model="claude-3-5-haiku-20241022",
            max_tokens=2000,
        )
        
        self._total_cost += response.cost
        
        # Parse response and create Story objects
        # For now, return sample stories
        return [
            Story(
                id=uuid4(),
                headline="Sample Story 1",
                summary="This is a sample story for testing.",
                zones=["horn_of_africa"],
            ),
        ]
    
    async def _generate_article(self, story: Story) -> ArticleOutput | None:
        """
        Generate a complete article for a story.
        
        Single-pass process:
        1. Analyze motivations and chains
        2. Generate article
        3. Light edit pass
        """
        try:
            # Combined analysis + writing prompt
            prompt = f"""You are a senior geopolitical analyst for The Undertow, an intelligence 
newsletter for sophisticated readers.

STORY: {story.headline}
SUMMARY: {story.summary}
ZONE: {', '.join(story.zones)}

Write a complete analytical article following this structure:

## THE HOOK (200 words)
What makes this matter beyond the obvious headline.

## WHAT HAPPENED
Precise reconstruction of events.

## THE MOTIVATION ANALYSIS
Analyze at 4 layers:
1. Individual decision-maker (their position, pressures, psychology)
2. Institutional interests (bureaucratic equities)
3. Structural pressures (what any actor would face)
4. Why now? (what opened the window)

## THE CHAINS
Trace consequences to 4th order:
- First order: Direct effects
- Second order: Responses
- Third order: Systemic adaptations
- Fourth order: Equilibrium shifts

## THE SUBTLETIES
What's being signaled, to whom, through what channels.
What silences are eloquent.

## THE TAKEAWAY
Why this matters beyond the news cycle.

VOICE: Dense, analytical, witty but serious. No clichés like "time will tell" or 
"in today's interconnected world". Active voice. Specific, not vague.

Write 1500-2000 words total."""

            response = await self._router.complete(
                prompt=prompt,
                model="claude-3-5-haiku-20241022",  # Cheap but good
                max_tokens=4000,
            )
            
            article_cost = response.cost
            self._total_cost += article_cost
            
            content = response.content
            
            # Light editing pass
            edit_prompt = f"""Review this article for:
1. Any clichéd phrases to remove
2. Passive voice to convert to active
3. Vague statements to make specific

Make minimal changes. Return the edited article only.

ARTICLE:
{content}"""

            edit_response = await self._router.complete(
                prompt=edit_prompt,
                model="claude-3-5-haiku-20241022",
                max_tokens=4000,
            )
            
            article_cost += edit_response.cost
            self._total_cost += edit_response.cost
            
            return ArticleOutput(
                headline=story.headline,
                content=edit_response.content,
                summary=story.summary,
                zones=story.zones,
                quality_score=0.85,  # Auto-pass, no human review
                cost=article_cost,
            )
        
        except Exception as e:
            logger.error("article_generation_failed", story=story.headline, error=str(e))
            return None
    
    def _to_article(self, output: ArticleOutput) -> Article:
        """Convert ArticleOutput to Article model."""
        return Article(
            id=uuid4(),
            headline=output.headline,
            content=output.content,
            summary=output.summary,
            zones=output.zones,
            quality_score=output.quality_score,
            status="published",
            created_at=datetime.utcnow(),
        )


# Singleton
_orchestrator: SimpleOrchestrator | None = None


def get_simple_orchestrator() -> SimpleOrchestrator:
    """Get or create the simple orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = SimpleOrchestrator()
    return _orchestrator

