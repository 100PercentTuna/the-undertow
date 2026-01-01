"""
Connection Analysis Agent.

Non-obvious connections - finding the "wow" insights that link
disparate events and reveal hidden dynamics.
"""

from typing import ClassVar

import structlog

from undertow.agents.base import BaseAgent
from undertow.exceptions import OutputParseError
from undertow.llm.tiers import ModelTier
from undertow.schemas.agents.connections import ConnectionsInput, ConnectionsOutput

logger = structlog.get_logger()


CONNECTIONS_SYSTEM_PROMPT = """You are the Connection Analysis agent for The Undertow.

Your role is to find NON-OBVIOUS CONNECTIONS - the insights that make readers say "wow,
I never thought of it that way." These are the connections that conventional analysis misses.

## WHAT TO FIND

### 1. Structural Analogues
What situations share the same UNDERLYING DYNAMIC with different actors?

Look for:
- Same game, different players
- Same structural pressures, different contexts
- Mirror images (same actors, opposite situations)
- Cross-regional patterns (what's happening elsewhere following same logic?)

Example: "China-Solomon Islands is structurally analogous to Israel-Somaliland - 
major power cultivating small state in strategic location, disrupting regional order."

### 2. Historical Parallels
What PAST EVENTS illuminate the present that aren't being commonly cited?

Look for:
- Overlooked historical precedents
- Patterns that repeat with variations
- Lessons from history being ignored
- "This is like X, but nobody's mentioning X"

### 3. Strange Bedfellows
What UNEXPECTED ALIGNMENTS are forming?

Look for:
- Actors cooperating who shouldn't be
- Temporary convergences of interest
- Enemy's enemy dynamics
- Ideological opposites finding common ground

Example: "Ethiopia (Christian-majority but Muslim government) + Israel + UAE + Somaliland 
(Muslim) = alignment cutting across religious lines. What unites them? Common opposition 
to Qatar, Turkey, Muslim Brotherhood-aligned actors, and Iranian influence."

### 4. Invisible Third Parties
Who is being SIGNALED TO without being named?

Look for:
- Real targets of diplomatic messaging
- Parties affected but not mentioned
- Audiences beyond the obvious
- Those whose silence is being purchased

### 5. Money Trails
Where is money FLOWING that connects to this event?

Look for:
- Commercial deals accompanying diplomatic moves
- Investment stakes in outcomes
- Specific companies and individuals benefiting
- Economic geography underlying political choices

### 6. Theoretical Lenses
What IR THEORY illuminates hidden dynamics?

Consider:
- Realism: Power, security, relative gains
- Liberalism: Institutions, interdependence, domestic politics
- Constructivism: Identity, norms, meaning-making
- Power transition: Hegemonic shifts, windows of opportunity
- Network theory: Nodes, hubs, structural holes
- Political economy: Who benefits materially?

## OUTPUT REQUIREMENTS

1. Find at least 2 structural analogues
2. Identify at least 1 overlooked historical parallel
3. Note any strange bedfellows
4. Identify invisible third parties
5. Follow money where relevant
6. Apply at least one theoretical lens
7. Synthesize the most illuminating connection

Be creative but grounded. Every connection must be defensible.

Output as valid JSON matching ConnectionsOutput schema."""


class ConnectionAnalysisAgent(BaseAgent[ConnectionsInput, ConnectionsOutput]):
    """
    Connection Analysis agent - finds non-obvious links.

    Uses FRONTIER tier for creative but grounded insights.
    """

    task_name: ClassVar[str] = "connection_analysis"
    version: ClassVar[str] = "1.0.0"
    input_schema: ClassVar[type] = ConnectionsInput
    output_schema: ClassVar[type] = ConnectionsOutput
    default_tier: ClassVar[ModelTier] = ModelTier.FRONTIER

    def _build_messages(self, input_data: ConnectionsInput) -> list[dict[str, str]]:
        """Build messages for connection analysis."""
        motivation_text = ""
        if input_data.motivation_synthesis:
            motivation_text = f"\n\n## MOTIVATION ANALYSIS\n{input_data.motivation_synthesis}"

        chains_text = ""
        if input_data.chains_synthesis:
            chains_text = f"\n\n## CHAINS ANALYSIS\n{input_data.chains_synthesis}"

        user_content = f"""## STORY TO ANALYZE

**Headline**: {input_data.story.headline}

**Summary**: {input_data.story.summary}

**Key Events**:
{chr(10).join(f'- {e}' for e in input_data.story.key_events) or 'Not specified'}

**Primary Actors**:
{chr(10).join(f'- {a}' for a in input_data.story.primary_actors) or 'Not specified'}

**Zones**: {', '.join(input_data.story.zones_affected) or 'Global'}
{motivation_text}
{chains_text}

## YOUR TASK

Find the non-obvious connections:
1. What structural analogues exist in other contexts?
2. What historical parallels are being overlooked?
3. What strange bedfellows are forming?
4. Who are the invisible third parties?
5. Where does the money lead?
6. What theoretical lens is most illuminating?

Give us the "wow" insights. Be creative but grounded.

Output as valid JSON matching ConnectionsOutput schema."""

        return [
            {"role": "system", "content": CONNECTIONS_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

    def _parse_output(self, content: str) -> ConnectionsOutput:
        """Parse connection analysis output."""
        try:
            data = self._extract_json(content)
            return ConnectionsOutput.model_validate(data)
        except Exception as e:
            logger.error("Failed to parse connections output", error=str(e))
            raise OutputParseError(
                agent_name=self.task_name,
                error=str(e),
                raw_output=content,
            ) from e

    async def _assess_quality(
        self,
        output: ConnectionsOutput,
        input_data: ConnectionsInput,
    ) -> float:
        """Assess quality of connection analysis."""
        scores: list[float] = []

        # Did we find connections?
        total_connections = (
            len(output.structural_analogues)
            + len(output.historical_parallels)
            + len(output.strange_bedfellows)
            + len(output.invisible_third_parties)
            + len(output.money_trails)
            + len(output.theoretical_lenses)
        )
        if total_connections >= 5:
            scores.append(1.0)
        elif total_connections >= 3:
            scores.append(0.7)
        else:
            scores.append(0.4)

        # Structural analogues depth
        for analogue in output.structural_analogues:
            if len(analogue.structural_similarity) >= 100:
                scores.append(1.0)
            elif len(analogue.structural_similarity) >= 50:
                scores.append(0.7)
            else:
                scores.append(0.5)

        # Synthesis quality
        if len(output.synthesis.most_illuminating_connection) >= 100:
            scores.append(1.0)
        elif len(output.synthesis.most_illuminating_connection) >= 50:
            scores.append(0.7)
        else:
            scores.append(0.4)

        # What conventional analysis misses
        if len(output.synthesis.what_conventional_analysis_misses) >= 50:
            scores.append(1.0)
        else:
            scores.append(0.6)

        return sum(scores) / max(len(scores), 1)

