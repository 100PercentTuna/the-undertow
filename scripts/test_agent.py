#!/usr/bin/env python
"""
Script to test an agent with sample data.

Usage:
    python scripts/test_agent.py motivation
    python scripts/test_agent.py chains
    python scripts/test_agent.py debate
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from undertow.config import settings
from undertow.llm.router import ModelRouter
from undertow.llm.providers.anthropic import AnthropicProvider
from undertow.llm.providers.openai import OpenAIProvider


async def test_motivation_agent():
    """Test the Motivation Analysis Agent."""
    from undertow.agents.analysis.motivation import MotivationAnalysisAgent
    from undertow.schemas.agents.motivation import (
        MotivationInput,
        StoryContext,
        AnalysisContext,
    )

    router = create_router()
    agent = MotivationAnalysisAgent(router, temperature=0.7)

    input_data = MotivationInput(
        story=StoryContext(
            headline="Country X Announces Surprise Recognition of Breakaway Region Y",
            summary="""In a dramatic diplomatic move, Country X officially recognized 
            the independence of Region Y, which broke away from Country Z two decades ago. 
            The recognition comes amid rising tensions between Country X and Country Z, 
            and has significant implications for regional stability.""",
            key_events=[
                "Official recognition announced at press conference",
                "Embassy opening planned for next month",
                "Trade agreement signed simultaneously",
                "Country Z recalls ambassador in protest",
            ],
            primary_actors=[
                "Leader of Country X",
                "Government of Region Y",
                "Country Z foreign ministry",
            ],
            zones_affected=["region_alpha", "region_beta"],
        ),
        context=AnalysisContext(
            historical_context="Region Y declared independence 20 years ago after conflict.",
            regional_context="Rising tensions between major powers in the region.",
        ),
    )

    print("Running Motivation Analysis Agent...")
    print("=" * 50)

    result = await agent.run(input_data)

    if result.success:
        print(f"Success! Quality Score: {result.metadata.quality_score}")
        print(f"Cost: ${result.metadata.cost_usd:.4f}")
        print(f"Primary Driver: {result.output.synthesis.primary_driver}")
        print(f"Explanation: {result.output.synthesis.primary_driver_explanation[:200]}...")
    else:
        print(f"Failed: {result.error}")

    return result


async def test_chains_agent():
    """Test the Chain Mapping Agent."""
    from undertow.agents.analysis.chains import ChainMappingAgent
    from undertow.schemas.agents.chains import ChainsInput
    from undertow.schemas.agents.motivation import StoryContext, AnalysisContext

    router = create_router()
    agent = ChainMappingAgent(router, temperature=0.7)

    input_data = ChainsInput(
        story=StoryContext(
            headline="Major Power Announces New Military Base Agreement",
            summary="""A major power has signed an agreement to establish a military 
            base in a strategically located small nation. The agreement grants 
            25-year access rights and includes infrastructure development.""",
            key_events=[
                "Agreement signed during state visit",
                "Base to be operational within 2 years",
                "Local opposition protests",
                "Regional powers express concern",
            ],
            primary_actors=[
                "Major power defense minister",
                "Small nation president",
                "Opposition coalition",
            ],
            zones_affected=["strategic_zone", "neighboring_zone"],
        ),
        context=AnalysisContext(
            historical_context="Region has been contested sphere of influence.",
        ),
        motivation_synthesis="Primary driver appears to be structural pressure to "
        "secure strategic access amid great power competition.",
    )

    print("Running Chain Mapping Agent...")
    print("=" * 50)

    result = await agent.run(input_data)

    if result.success:
        print(f"Success! Quality Score: {result.metadata.quality_score}")
        print(f"Cost: ${result.metadata.cost_usd:.4f}")
        print(f"Most Significant: {result.output.synthesis.most_significant_consequence[:150]}...")
        print(f"Hidden Game: {result.output.synthesis.hidden_game_hypothesis[:150]}...")
    else:
        print(f"Failed: {result.error}")

    return result


def create_router() -> ModelRouter:
    """Create a model router with available providers."""
    providers = {}

    if settings.anthropic_api_key:
        providers["anthropic"] = AnthropicProvider(settings.anthropic_api_key)
        print("✓ Anthropic provider configured")

    if settings.openai_api_key:
        providers["openai"] = OpenAIProvider(settings.openai_api_key)
        print("✓ OpenAI provider configured")

    if not providers:
        raise ValueError(
            "No LLM providers configured. "
            "Set ANTHROPIC_API_KEY or OPENAI_API_KEY in environment."
        )

    return ModelRouter(
        providers=providers,
        preference=settings.ai_provider_preference.value,
        daily_budget=settings.ai_daily_budget_usd,
    )


async def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_agent.py <agent_name>")
        print("  Agents: motivation, chains")
        sys.exit(1)

    agent_name = sys.argv[1].lower()

    if agent_name == "motivation":
        await test_motivation_agent()
    elif agent_name == "chains":
        await test_chains_agent()
    else:
        print(f"Unknown agent: {agent_name}")
        print("Available: motivation, chains")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

