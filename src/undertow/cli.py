"""
Command-line interface for The Undertow.

Usage:
    python -m undertow.cli <command> [options]

Commands:
    serve       Start the API server
    pipeline    Run the daily pipeline
    analyze     Analyze a specific story
    ingest      Ingest from sources
    stats       Show system statistics
"""

import asyncio
import sys
from datetime import datetime
from typing import Optional

import structlog

# Configure logging before imports
from undertow.infrastructure.logging import setup_logging

setup_logging()

logger = structlog.get_logger()


def main() -> int:
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    command = sys.argv[1]
    args = sys.argv[2:]

    commands = {
        "serve": cmd_serve,
        "pipeline": cmd_pipeline,
        "analyze": cmd_analyze,
        "ingest": cmd_ingest,
        "stats": cmd_stats,
        "test-agent": cmd_test_agent,
        "help": cmd_help,
    }

    if command not in commands:
        print(f"Unknown command: {command}")
        print(__doc__)
        return 1

    try:
        return commands[command](args)
    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 130
    except Exception as e:
        logger.error("Command failed", command=command, error=str(e))
        print(f"Error: {e}")
        return 1


def cmd_serve(args: list[str]) -> int:
    """Start the API server."""
    import uvicorn

    host = "127.0.0.1"
    port = 8000
    reload = "--reload" in args

    # Parse args
    for i, arg in enumerate(args):
        if arg == "--host" and i + 1 < len(args):
            host = args[i + 1]
        elif arg == "--port" and i + 1 < len(args):
            port = int(args[i + 1])

    print(f"Starting server at http://{host}:{port}")
    uvicorn.run(
        "undertow.api.main:app",
        host=host,
        port=port,
        reload=reload,
    )
    return 0


def cmd_pipeline(args: list[str]) -> int:
    """Run the daily pipeline."""
    from undertow.tasks.pipeline import run_daily_pipeline

    print("Starting daily pipeline...")
    result = run_daily_pipeline()

    print(f"Pipeline completed:")
    print(f"  Run ID: {result.get('run_id', 'N/A')}")
    print(f"  Status: {result.get('status', 'N/A')}")
    print(f"  Stories processed: {result.get('stories_processed', 0)}")
    print(f"  Articles generated: {result.get('articles_generated', 0)}")
    print(f"  Total cost: ${result.get('total_cost', 0):.2f}")

    return 0 if result.get("status") == "completed" else 1


def cmd_analyze(args: list[str]) -> int:
    """Analyze a specific story."""
    if not args:
        print("Usage: analyze <story_id>")
        return 1

    story_id = args[0]
    from undertow.tasks.pipeline import analyze_story

    print(f"Analyzing story {story_id}...")
    result = analyze_story(story_id)

    print(f"Analysis completed:")
    print(f"  Success: {result.get('success', False)}")
    print(f"  Quality scores: {result.get('quality_scores', {})}")
    print(f"  Cost: ${result.get('total_cost', 0):.2f}")

    if result.get("error"):
        print(f"  Error: {result.get('error')}")

    return 0 if result.get("success") else 1


def cmd_ingest(args: list[str]) -> int:
    """Ingest from sources."""
    from undertow.tasks.ingestion import ingest_all_sources

    print("Starting source ingestion...")
    result = ingest_all_sources()

    print(f"Ingestion completed:")
    print(f"  Feeds processed: {result.get('feeds_processed', 0)}")
    print(f"  Stories fetched: {result.get('stories_fetched', 0)}")
    print(f"  Stories added: {result.get('stories_added', 0)}")

    if result.get("errors"):
        print(f"  Errors: {len(result.get('errors', []))}")

    return 0


def cmd_stats(args: list[str]) -> int:
    """Show system statistics."""
    asyncio.run(_async_stats())
    return 0


async def _async_stats() -> None:
    """Async stats implementation."""
    from undertow.infrastructure.database import init_db, get_session
    from undertow.repositories import StoryRepository, ArticleRepository, PipelineRepository

    await init_db()

    async for session in get_session():
        story_repo = StoryRepository(session)
        article_repo = ArticleRepository(session)
        pipeline_repo = PipelineRepository(session)

        # Get counts
        story_counts = await story_repo.count_by_status()
        article_stats = await article_repo.get_stats()
        pipeline_stats = await pipeline_repo.get_stats(days=7)

        print("\n=== THE UNDERTOW STATS ===\n")

        print("STORIES:")
        for status, count in story_counts.items():
            print(f"  {status}: {count}")
        print(f"  Total: {sum(story_counts.values())}")

        print("\nARTICLES:")
        for status, count in article_stats.get("by_status", {}).items():
            print(f"  {status}: {count}")
        print(f"  Average quality: {article_stats.get('avg_quality_score', 0):.2f}")
        print(f"  Published today: {article_stats.get('published_today', 0)}")

        print("\nPIPELINE (last 7 days):")
        print(f"  Total runs: {pipeline_stats.get('total_runs', 0)}")
        print(f"  Success rate: {pipeline_stats.get('success_rate', 0) * 100:.1f}%")
        print(f"  Stories processed: {pipeline_stats.get('stories_processed', 0)}")
        print(f"  Total cost: ${pipeline_stats.get('total_cost_usd', 0):.2f}")

        print()


def cmd_test_agent(args: list[str]) -> int:
    """Test an agent with sample data."""
    if not args:
        print("Usage: test-agent <agent_name>")
        print("  Agents: motivation, chains, challenger, writer")
        return 1

    agent_name = args[0].lower()
    asyncio.run(_test_agent(agent_name))
    return 0


async def _test_agent(agent_name: str) -> None:
    """Run agent test."""
    from undertow.config import settings
    from undertow.llm.router import ModelRouter
    from undertow.llm.providers.anthropic import AnthropicProvider
    from undertow.llm.providers.openai import OpenAIProvider

    # Create router
    providers = {}
    if settings.anthropic_api_key:
        providers["anthropic"] = AnthropicProvider(settings.anthropic_api_key)
    if settings.openai_api_key:
        providers["openai"] = OpenAIProvider(settings.openai_api_key)

    if not providers:
        print("Error: No API keys configured")
        return

    router = ModelRouter(providers=providers, preference="anthropic")

    if agent_name == "motivation":
        await _test_motivation(router)
    elif agent_name == "chains":
        await _test_chains(router)
    elif agent_name == "challenger":
        await _test_challenger(router)
    else:
        print(f"Unknown agent: {agent_name}")


async def _test_motivation(router) -> None:
    """Test motivation agent."""
    from undertow.agents.analysis.motivation import MotivationAnalysisAgent
    from undertow.schemas.agents.motivation import (
        MotivationInput, StoryContext, AnalysisContext
    )

    agent = MotivationAnalysisAgent(router)

    input_data = MotivationInput(
        story=StoryContext(
            headline="Test Country Announces Surprise Policy Shift",
            summary="A test country has announced a significant policy change that "
                    "affects regional dynamics and great power competition.",
            key_events=["Policy announced", "Reactions from neighbors"],
            primary_actors=["Test Leader", "Test Government"],
            zones_affected=["test_zone"],
        ),
        context=AnalysisContext(),
    )

    print("Running Motivation Analysis...")
    result = await agent.run(input_data)

    if result.success:
        print(f"✓ Success! Quality: {result.metadata.quality_score:.2f}")
        print(f"  Cost: ${result.metadata.cost_usd:.4f}")
        print(f"  Primary driver: {result.output.synthesis.primary_driver}")
    else:
        print(f"✗ Failed: {result.error}")


async def _test_chains(router) -> None:
    """Test chains agent."""
    from undertow.agents.analysis.chains import ChainMappingAgent
    from undertow.schemas.agents.chains import ChainsInput
    from undertow.schemas.agents.motivation import StoryContext, AnalysisContext

    agent = ChainMappingAgent(router)

    input_data = ChainsInput(
        story=StoryContext(
            headline="Major Power Expands Military Presence",
            summary="A major power has expanded its military presence in a "
                    "strategically important region.",
            key_events=["Base agreement signed", "Regional reactions"],
            primary_actors=["Major Power", "Host Country"],
            zones_affected=["strategic_zone"],
        ),
        context=AnalysisContext(),
    )

    print("Running Chain Mapping...")
    result = await agent.run(input_data)

    if result.success:
        print(f"✓ Success! Quality: {result.metadata.quality_score:.2f}")
        print(f"  Cost: ${result.metadata.cost_usd:.4f}")
        print(f"  Hidden game: {result.output.synthesis.hidden_game_hypothesis[:100]}...")
    else:
        print(f"✗ Failed: {result.error}")


async def _test_challenger(router) -> None:
    """Test challenger agent."""
    from undertow.agents.adversarial.debate import ChallengerAgent
    from undertow.schemas.agents.debate import ChallengerInput

    agent = ChallengerAgent(router)

    input_data = ChallengerInput(
        analysis_summary="The leader's primary motivation was domestic politics, "
                         "seeking to shore up nationalist support ahead of elections.",
        key_claims=[
            "The timing was driven by election considerations",
            "Nationalist base was the primary audience",
            "Economic factors were secondary",
        ],
    )

    print("Running Challenger Agent...")
    result = await agent.run(input_data)

    if result.success:
        print(f"✓ Success! Quality: {result.metadata.quality_score:.2f}")
        print(f"  Cost: ${result.metadata.cost_usd:.4f}")
        print(f"  Challenges raised: {len(result.output.challenges)}")
        for c in result.output.challenges:
            print(f"    - [{c.severity}] {c.challenge_type}: {c.target_claim[:50]}...")
    else:
        print(f"✗ Failed: {result.error}")


def cmd_help(args: list[str]) -> int:
    """Show help."""
    print(__doc__)
    print("\nCommands:")
    print("  serve              Start the API server")
    print("    --host HOST      Host to bind to (default: 127.0.0.1)")
    print("    --port PORT      Port to bind to (default: 8000)")
    print("    --reload         Enable auto-reload")
    print()
    print("  pipeline           Run the daily pipeline manually")
    print()
    print("  analyze <id>       Analyze a specific story by ID")
    print()
    print("  ingest             Ingest from all configured sources")
    print()
    print("  stats              Show system statistics")
    print()
    print("  test-agent <name>  Test an agent (motivation, chains, challenger)")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())

