"""
Geometry Analysis Agent.

The map always matters - strategic geography analysis.
Every decision exists in physical space.
"""

from typing import ClassVar

import structlog

from undertow.agents.base import BaseAgent
from undertow.exceptions import OutputParseError
from undertow.llm.tiers import ModelTier
from undertow.schemas.agents.geometry import GeometryInput, GeometryOutput

logger = structlog.get_logger()


GEOMETRY_SYSTEM_PROMPT = """You are the Geometry Analysis agent for The Undertow.

Your role is to analyze the GEOGRAPHIC LOGIC of events. The map always matters.
Every decision exists in physical space. Geography creates imperatives.

## THE GEOGRAPHIC LOGIC FRAMEWORK

### 1. Chokepoints
Is this near a strait, canal, narrow passage?

Key chokepoints to consider:
- Strait of Hormuz (Persian Gulf oil)
- Bab el-Mandeb (Red Sea/Suez access)
- Strait of Malacca (Asia-Pacific trade)
- Suez Canal (Europe-Asia)
- Panama Canal (Atlantic-Pacific)
- Turkish Straits (Black Sea access)
- GIUK Gap (North Atlantic)
- Suwalki Gap (Baltic-Poland corridor)

### 2. Maritime Access
How does this affect sea lanes, port access, naval basing?

Consider:
- Port access and control
- Sea lane security
- Naval basing rights
- Freedom of navigation

### 3. Land Corridors
How does this affect overland routes?

Consider:
- Trade routes
- Military movement corridors
- Pipeline routes
- Rail connections

### 4. Buffer Zones
Is this about creating or eliminating buffer space?

Consider:
- Whose security perimeter?
- Historical buffer arrangements
- Buffer erosion or expansion

### 5. Resource Proximity
What resources are nearby?

Consider:
- Energy (oil, gas, renewables)
- Minerals (rare earths, lithium, cobalt)
- Water (rivers, aquifers)
- Agricultural land

### 6. Network Position
How does this fit into larger networks?

Consider:
- What other positions does this actor hold?
- Is this part of a pattern?
- Does this create alternatives/redundancy?
- Does this interfere with rival networks?

## THE DENIAL DIMENSION

Always ask: What's denied to adversaries?
- Access?
- Influence?
- Intelligence?
- Economic opportunity?

## OUTPUT REQUIREMENTS

1. Identify relevant chokepoints
2. Analyze access implications
3. Map network positioning
4. Assess resource geography
5. Evaluate buffer zones
6. Synthesize the geographic logic

Think like a strategist looking at a map. What does geography tell us that words don't?

Output as valid JSON matching GeometryOutput schema."""


class GeometryAnalysisAgent(BaseAgent[GeometryInput, GeometryOutput]):
    """
    Geometry Analysis agent - strategic geography analysis.

    Uses HIGH tier for comprehensive geographic reasoning.
    """

    task_name: ClassVar[str] = "geometry_analysis"
    version: ClassVar[str] = "1.0.0"
    input_schema: ClassVar[type] = GeometryInput
    output_schema: ClassVar[type] = GeometryOutput
    default_tier: ClassVar[ModelTier] = ModelTier.HIGH

    def _build_messages(self, input_data: GeometryInput) -> list[dict[str, str]]:
        """Build messages for geometry analysis."""
        location_text = ""
        if input_data.location_details:
            location_text = f"\n\n## LOCATION DETAILS\n{input_data.location_details}"

        infra_text = ""
        if input_data.relevant_infrastructure:
            infra_text = "\n\n## RELEVANT INFRASTRUCTURE\n" + "\n".join(
                f"- {i}" for i in input_data.relevant_infrastructure
            )

        user_content = f"""## STORY TO ANALYZE

**Headline**: {input_data.story.headline}

**Summary**: {input_data.story.summary}

**Key Events**:
{chr(10).join(f'- {e}' for e in input_data.story.key_events) or 'Not specified'}

**Primary Actors**:
{chr(10).join(f'- {a}' for a in input_data.story.primary_actors) or 'Not specified'}

**Zones**: {', '.join(input_data.story.zones_affected) or 'Global'}
{location_text}
{infra_text}

## YOUR TASK

Pull out the map and analyze:
1. What chokepoints are relevant?
2. How does this change access?
3. What network positioning is happening?
4. What resources are in play?
5. How do buffer zones factor in?

Synthesize the geographic logic - what does the map reveal?

Output as valid JSON matching GeometryOutput schema."""

        return [
            {"role": "system", "content": GEOMETRY_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

    def _parse_output(self, content: str) -> GeometryOutput:
        """Parse geometry analysis output."""
        try:
            data = self._extract_json(content)
            return GeometryOutput.model_validate(data)
        except Exception as e:
            logger.error("Failed to parse geometry output", error=str(e))
            raise OutputParseError(
                agent_name=self.task_name,
                error=str(e),
                raw_output=content,
            ) from e

    async def _assess_quality(
        self,
        output: GeometryOutput,
        input_data: GeometryInput,
    ) -> float:
        """Assess quality of geometry analysis."""
        scores: list[float] = []

        # Did we identify geographic elements?
        elements_found = (
            len(output.chokepoints)
            + len(output.access_analysis)
            + len(output.network_positions)
            + len(output.resource_proximity)
            + len(output.buffer_zones)
        )
        if elements_found >= 3:
            scores.append(1.0)
        elif elements_found >= 1:
            scores.append(0.7)
        else:
            scores.append(0.3)

        # Synthesis quality
        if len(output.synthesis.primary_geographic_logic) >= 100:
            scores.append(1.0)
        elif len(output.synthesis.primary_geographic_logic) >= 50:
            scores.append(0.7)
        else:
            scores.append(0.4)

        # Map reveals insight
        if len(output.synthesis.what_map_reveals) >= 50:
            scores.append(1.0)
        else:
            scores.append(0.6)

        return sum(scores) / len(scores)

