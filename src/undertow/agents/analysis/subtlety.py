"""
Subtlety Analysis Agent.

Decodes what's being said without being said - the five channels
of diplomatic communication.
"""

from typing import ClassVar

import structlog

from undertow.agents.base import BaseAgent
from undertow.exceptions import OutputParseError
from undertow.llm.tiers import ModelTier
from undertow.schemas.agents.subtlety import SubtletyInput, SubtletyOutput

logger = structlog.get_logger()


SUBTLETY_SYSTEM_PROMPT = """You are the Subtlety Analysis agent for The Undertow.

Your role is to decode what's being communicated WITHOUT being said explicitly.
International relations operates on multiple simultaneous channels. The public
statement is often the least informative.

## THE FIVE CHANNELS

### 1. The Signal in the Action
Every diplomatic action is also a message, often to someone other than the direct party.

Analyze:
- **Intended Audiences**: Who is this REALLY addressed to? Often not the obvious party.
- **Norm Invoked/Violated**: What principle is being upheld or challenged?
- **Capability Demonstrated**: "We can do things you didn't expect."
- **Commitment Signaled**: Hard-to-reverse actions signal durable interest.
- **Counterfactual Signal**: What would it have meant NOT to do this?

### 2. The Eloquent Silence
What's NOT being said, and by whom?

Analyze:
- **Who Hasn't Commented**: Major player silence is a statement.
- **Missing from Framing**: What's conspicuously absent?
- **Deflected Questions**: When officials evade, the evasion is data.
- **Dogs That Didn't Bark**: Expected opposition that didn't materialize.

### 3. The Timing Message
WHEN something happens is often as important as WHAT happens.

Analyze:
- **Sequence**: What preceded/follows? What's being bracketed or overshadowed?
- **Calendar Context**: Elections? UN session? Summit? Symbolic date?
- **Sequence Position**: Early (creating facts) or late (responding)?
- **Window**: Is there "now or never" quality?

### 4. The Choreography
HOW something is staged communicates independently of content.

Analyze:
- **Venue**: Leaders traveling vs. hosting. Public vs. private.
- **Protocol Level**: Foreign minister vs. head of state.
- **Visual Arrangement**: Flags? Who stood where? Documents signed?
- **Domestic Framing**: How each side presents to their audience.
- **Inclusions/Exclusions**: Who was/wasn't there?

### 5. Deniable Communication
What's being said through unofficial channels?

Analyze:
- **Unnamed Officials**: Authorized leaks carry messages too sensitive for record.
- **Sympathetic Media**: Trial balloons and warnings in predictable outlets.
- **Proxy Statements**: Allies say what officials can't.
- **Back-Channels**: Track-2, traditional mediators.

## OUTPUT REQUIREMENTS

1. Analyze all five channels
2. Identify the PRIMARY hidden message
3. List audiences beyond the obvious
4. Assess sophistication of signaling
5. State confidence level

Be specific. Cite evidence. Distinguish inference from speculation.

Output as valid JSON matching SubtletyOutput schema."""


class SubtletyAnalysisAgent(BaseAgent[SubtletyInput, SubtletyOutput]):
    """
    Subtlety Analysis agent - decodes diplomatic signaling.

    Uses HIGH tier for nuanced interpretation.
    """

    task_name: ClassVar[str] = "subtlety_analysis"
    version: ClassVar[str] = "1.0.0"
    input_schema: ClassVar[type] = SubtletyInput
    output_schema: ClassVar[type] = SubtletyOutput
    default_tier: ClassVar[ModelTier] = ModelTier.HIGH

    def _build_messages(self, input_data: SubtletyInput) -> list[dict[str, str]]:
        """Build messages for subtlety analysis."""
        statements_text = ""
        if input_data.public_statements:
            statements_text = "\n\n## PUBLIC STATEMENTS\n" + "\n".join(
                f"- {s}" for s in input_data.public_statements
            )

        coverage_text = ""
        if input_data.media_coverage:
            coverage_text = "\n\n## MEDIA COVERAGE\n" + "\n".join(
                f"- {c}" for c in input_data.media_coverage
            )

        user_content = f"""## STORY TO ANALYZE

**Headline**: {input_data.story.headline}

**Summary**: {input_data.story.summary}

**Key Events**:
{chr(10).join(f'- {e}' for e in input_data.story.key_events) or 'Not specified'}

**Primary Actors**:
{chr(10).join(f'- {a}' for a in input_data.story.primary_actors) or 'Not specified'}

**Zones**: {', '.join(input_data.story.zones_affected) or 'Global'}
{statements_text}
{coverage_text}

## YOUR TASK

Decode the subtleties:
1. What's the signal in the action?
2. What do the silences tell us?
3. Why this timing specifically?
4. What does the choreography communicate?
5. What's being said through deniable channels?

Synthesize into primary hidden message and key audiences.

Output as valid JSON matching SubtletyOutput schema."""

        return [
            {"role": "system", "content": SUBTLETY_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

    def _parse_output(self, content: str) -> SubtletyOutput:
        """Parse subtlety analysis output."""
        try:
            data = self._extract_json(content)
            return SubtletyOutput.model_validate(data)
        except Exception as e:
            logger.error("Failed to parse subtlety output", error=str(e))
            raise OutputParseError(
                agent_name=self.task_name,
                error=str(e),
                raw_output=content,
            ) from e

    async def _assess_quality(
        self,
        output: SubtletyOutput,
        input_data: SubtletyInput,
    ) -> float:
        """Assess quality of subtlety analysis."""
        scores: list[float] = []

        # Signal analysis depth
        if len(output.signal_analysis.intended_audiences) >= 2:
            scores.append(1.0)
        elif len(output.signal_analysis.intended_audiences) >= 1:
            scores.append(0.7)
        else:
            scores.append(0.3)

        # Silence analysis
        if output.silence_analysis.notable_non_commenters:
            scores.append(1.0)
        else:
            scores.append(0.5)

        # Timing analysis depth
        if len(output.timing_analysis.timing_assessment) >= 50:
            scores.append(1.0)
        else:
            scores.append(0.6)

        # Synthesis quality
        if len(output.synthesis.primary_hidden_message) >= 100:
            scores.append(1.0)
        elif len(output.synthesis.primary_hidden_message) >= 50:
            scores.append(0.7)
        else:
            scores.append(0.4)

        # Audiences identified
        if len(output.synthesis.key_audiences_beyond_obvious) >= 2:
            scores.append(1.0)
        else:
            scores.append(0.6)

        return sum(scores) / len(scores)

