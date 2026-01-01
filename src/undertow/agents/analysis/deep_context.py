"""
Deep Context Agent.

The deep well - hidden context that loads the situation.
Every situation carries invisible weight.
"""

from typing import ClassVar

import structlog

from undertow.agents.base import BaseAgent
from undertow.exceptions import OutputParseError
from undertow.llm.tiers import ModelTier
from undertow.schemas.agents.deep_context import DeepContextInput, DeepContextOutput

logger = structlog.get_logger()


DEEP_CONTEXT_SYSTEM_PROMPT = """You are the Deep Context agent for The Undertow.

Your role is to surface the HIDDEN CONTEXT that loads every situation.
Every situation carries invisible weight—past grievances, debts, patterns,
traumas that shape perception even when unspoken.

## WHAT TO ANALYZE

### 1. Historical Grievances
Remembered wrongs that shape collective memory.

Look for:
- Past conflicts, occupations, humiliations
- Territorial losses
- Broken promises
- Massacres, expulsions, atrocities
- Colonial legacies

### 2. Unpaid Debts
Who helped whom in past crises? What favors remain unreturned?

Look for:
- Past assistance during crises
- Political support given
- Economic bailouts
- Military backing
- Diplomatic cover provided

### 3. Pattern Recognition
"This is just like when..." is powerful in decision-making.

Look for:
- Historical parallels actors are invoking
- Lessons drawn from past experiences
- Formative events that shape worldview
- Precedents being cited or avoided

### 4. Elite Networks
Personal relationships between leaders and elites.

Look for:
- Shared education (same universities, military academies)
- Family/clan connections
- Business relationships
- Old friendships or enmities
- Military service together

### 5. Strategic Culture
Characteristic behavior patterns shaped by history.

Look for:
- Risk tolerance patterns
- Preferred instruments of statecraft
- Decision-making styles
- National "lessons" from history
- Taboos and red lines

### 6. Institutional Memory
What permanent bureaucracies "know" about handling situations.

Look for:
- Standard operating procedures
- Past successes/failures that shaped doctrine
- Institutional biases
- Career incentives

## OUTPUT REQUIREMENTS

1. Identify relevant historical grievances
2. Map unpaid political debts
3. Note pattern recognitions in play
4. Identify relevant elite networks
5. Surface strategic culture elements
6. Note institutional memories
7. Synthesize what outsiders typically miss

Be specific. Ground in history. Distinguish well-documented from inferred.

Output as valid JSON matching DeepContextOutput schema."""


class DeepContextAgent(BaseAgent[DeepContextInput, DeepContextOutput]):
    """
    Deep Context agent - historical and cultural loading.

    Uses FRONTIER tier for deep historical knowledge.
    """

    task_name: ClassVar[str] = "deep_context"
    version: ClassVar[str] = "1.0.0"
    input_schema: ClassVar[type] = DeepContextInput
    output_schema: ClassVar[type] = DeepContextOutput
    default_tier: ClassVar[ModelTier] = ModelTier.FRONTIER

    def _build_messages(self, input_data: DeepContextInput) -> list[dict[str, str]]:
        """Build messages for deep context analysis."""
        actors_text = ""
        if input_data.actors_to_analyze:
            actors_text = "\n\n## ACTORS TO DEEP-DIVE\n" + "\n".join(
                f"- {a}" for a in input_data.actors_to_analyze
            )

        user_content = f"""## STORY TO ANALYZE

**Headline**: {input_data.story.headline}

**Summary**: {input_data.story.summary}

**Key Events**:
{chr(10).join(f'- {e}' for e in input_data.story.key_events) or 'Not specified'}

**Primary Actors**:
{chr(10).join(f'- {a}' for a in input_data.story.primary_actors) or 'Not specified'}

**Zones**: {', '.join(input_data.story.zones_affected) or 'Global'}

**Historical Time Horizon**: {input_data.time_horizon}
{actors_text}

## YOUR TASK

Dig into the deep context:
1. What historical grievances load this situation?
2. What political debts are in play?
3. What historical patterns are actors seeing?
4. What elite networks matter?
5. What does strategic culture tell us?
6. What institutional memories are at work?

Synthesize: What do outsiders typically miss about this situation?

Output as valid JSON matching DeepContextOutput schema."""

        return [
            {"role": "system", "content": DEEP_CONTEXT_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

    def _parse_output(self, content: str) -> DeepContextOutput:
        """Parse deep context output."""
        try:
            data = self._extract_json(content)
            return DeepContextOutput.model_validate(data)
        except Exception as e:
            logger.error("Failed to parse deep context output", error=str(e))
            raise OutputParseError(
                agent_name=self.task_name,
                error=str(e),
                raw_output=content,
            ) from e

    async def _assess_quality(
        self,
        output: DeepContextOutput,
        input_data: DeepContextInput,
    ) -> float:
        """Assess quality of deep context analysis."""
        scores: list[float] = []

        # Did we find historical factors?
        elements_found = (
            len(output.historical_grievances)
            + len(output.unpaid_debts)
            + len(output.pattern_recognitions)
            + len(output.elite_networks)
            + len(output.strategic_culture)
            + len(output.institutional_memories)
        )
        if elements_found >= 4:
            scores.append(1.0)
        elif elements_found >= 2:
            scores.append(0.7)
        else:
            scores.append(0.4)

        # Synthesis quality
        if len(output.synthesis.most_salient_historical_factor) >= 100:
            scores.append(1.0)
        elif len(output.synthesis.most_salient_historical_factor) >= 50:
            scores.append(0.7)
        else:
            scores.append(0.4)

        # What outsiders miss
        if len(output.synthesis.what_outsiders_miss) >= 50:
            scores.append(1.0)
        else:
            scores.append(0.6)

        # Hidden constraints identified
        if output.synthesis.hidden_constraints:
            scores.append(1.0)
        else:
            scores.append(0.5)

        return sum(scores) / len(scores)

