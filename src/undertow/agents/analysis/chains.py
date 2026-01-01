"""
Chain Mapping Agent.

Traces consequences forward (ripple map) and backward (cui bono at each order).
"""

from typing import ClassVar

import structlog

from undertow.agents.base import BaseAgent
from undertow.exceptions import OutputParseError
from undertow.llm.tiers import ModelTier
from undertow.schemas.agents.chains import (
    ChainsInput,
    ChainsOutput,
)

logger = structlog.get_logger()


SYSTEM_PROMPT = """You are a senior intelligence analyst specializing in chain-of-consequence analysis for The Undertow, a world-class geopolitical intelligence publication.

Your task is to map consequences forward and backward from geopolitical events.

## FORWARD TRACING: THE RIPPLE MAP

Trace consequences out to the 4th or 5th order:

### First Order - Direct Consequences
What happens as a direct result of this action? A does X → B experiences Y.

### Second Order - Responses
How do affected parties respond? How does the original actor respond to their responses?

### Third Order - Systemic Adaptations
How do institutions, norms, and behavior patterns adapt?
- What precedents are set?
- What's now "possible" that seemed impossible?
- What norms are strengthened or weakened?

### Fourth Order - Equilibrium Shifts
What's the new stable state?
- What's the "new normal"?
- What structural changes persist?
- What future options are opened or closed?

### Fifth Order - Distant Ripples (if significant)
What happens when 4th-order effects interact with other 4th-order effects elsewhere?

## BACKWARD TRACING: CUI BONO AT THE NTH ORDER

Work backward from distant beneficiaries to identify hidden motivations:

1. Map all consequences out to 4-5 orders
2. For each consequence, ask: Who benefits?
3. For each beneficiary, ask: Did they have means to influence the original action?
4. Look for beneficiaries who:
   - Benefit significantly at the 3rd-5th order
   - Had plausible channels to influence Actor A
   - Have a pattern of similar indirect influence
   - Whose benefit seems too convenient to be accidental

## CONFIDENCE DECAY

CRITICAL: Confidence MUST decay at each order:
- First Order: Can be high (0.7-0.9) if well-sourced
- Second Order: Moderate-to-high (0.6-0.8)
- Third Order: Moderate (0.4-0.7)
- Fourth Order: Low-to-moderate (0.3-0.6)
- Fifth Order: Speculative (0.2-0.5)

## QUALITY STANDARDS

- Trace chains far enough to find the non-obvious
- The actual game often lives at the 4th or 5th order
- Ask "who benefits if I follow this out three more steps?"
- Consider attention economics: every crisis is also a distraction
- Map interaction points where multiple chains converge

Output your analysis as valid JSON matching the required schema."""


class ChainMappingAgent(BaseAgent[ChainsInput, ChainsOutput]):
    """
    Chain mapping agent for consequence tracing.

    Traces consequences forward (ripple map) and backward (cui bono)
    to reveal the actual game being played.

    Attributes:
        task_name: "chain_mapping"
        version: Current agent version
        default_tier: FRONTIER (requires best model quality)
    """

    task_name: ClassVar[str] = "chain_mapping"
    version: ClassVar[str] = "1.0.0"
    input_schema: ClassVar[type] = ChainsInput
    output_schema: ClassVar[type] = ChainsOutput
    default_tier: ClassVar[ModelTier] = ModelTier.FRONTIER

    def _build_messages(self, input_data: ChainsInput) -> list[dict[str, str]]:
        """Build messages for chain mapping."""
        user_content = self._format_user_prompt(input_data)

        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

    def _format_user_prompt(self, input_data: ChainsInput) -> str:
        """Format the user prompt with story context."""
        story = input_data.story
        context = input_data.context

        # Format key events
        events_text = "\n".join(f"- {event}" for event in story.key_events[:10])

        # Format actors if available
        actors_text = ""
        if context.actors:
            actors_text = "\n".join(
                f"- **{actor.name}** ({actor.role})"
                for actor in context.actors[:5]
            )
        else:
            actors_text = f"Primary actors: {', '.join(story.primary_actors)}"

        motivation_section = ""
        if input_data.motivation_synthesis:
            motivation_section = f"""
## MOTIVATION ANALYSIS SUMMARY (from prior analysis)
{input_data.motivation_synthesis}
"""

        return f"""## STORY TO ANALYZE

**Headline:** {story.headline}

**Summary:**
{story.summary}

**Key Events:**
{events_text}

**Actors:**
{actors_text}

**Zones Affected:** {', '.join(story.zones_affected)}
{motivation_section}
## CONTEXT

**Historical Context:**
{context.historical_context or "No specific historical context provided."}

**Regional Context:**
{context.regional_context or "No specific regional context provided."}

## YOUR TASK

Perform comprehensive chain mapping analysis:

### 1. RIPPLE MAP (Forward Tracing)
Trace consequences through five orders:
- First order: Direct consequences (high confidence)
- Second order: Responses to first order (moderate-high confidence)
- Third order: Systemic adaptations (moderate confidence)
- Fourth order: Equilibrium shifts (low-moderate confidence)
- Fifth order: Distant ripples (speculative, only if significant)

For each order:
- Identify 2-4 significant consequences
- Name affected actors
- Assess likelihood (0-1)
- Specify time horizon
- ENSURE confidence decays appropriately with each order

### 2. CUI BONO (Backward Tracing)
Work backward from beneficiaries:
- Obvious (first-order) beneficiaries
- Second-order beneficiaries
- Third-order beneficiaries
- Potentially hidden beneficiaries (those who benefit at 4th/5th order with means to influence)

For hidden beneficiaries, explicitly assess:
- Did they have means to influence the original action?
- What channels could they have used?
- How suspicious is this pattern?

### 3. CHAIN INTERACTIONS
Identify how this chain interacts with other ongoing chains:
- What parallel developments are relevant?
- Where do chains intersect?
- What emergent effects arise from interactions?

### 4. SYNTHESIS
Provide:
- The single most significant consequence (and which order)
- A "hidden game hypothesis" - what game is actually being played
- Watch indicators that would confirm/disconfirm your analysis
- A note on confidence decay
- Key information gaps

Output your complete analysis as valid JSON matching the ChainsOutput schema."""

    def _parse_output(self, content: str) -> ChainsOutput:
        """Parse the LLM response into ChainsOutput."""
        try:
            data = self._extract_json(content)
            return ChainsOutput.model_validate(data)
        except Exception as e:
            logger.error(
                "Failed to parse chains output",
                error=str(e),
                content_preview=content[:500],
            )
            raise OutputParseError(
                agent_name=self.task_name,
                error=str(e),
                raw_output=content,
            ) from e

    async def _assess_quality(
        self,
        output: ChainsOutput,
        input_data: ChainsInput,
    ) -> float:
        """Assess the quality of the chain analysis."""
        scores: list[tuple[str, float, float]] = []

        # 1. Confidence decay check
        decay_score = self._score_confidence_decay(output)
        scores.append(("confidence_decay", decay_score, 0.25))

        # 2. Chain completeness
        completeness = self._score_completeness(output)
        scores.append(("completeness", completeness, 0.25))

        # 3. Cui bono depth
        cui_bono = self._score_cui_bono(output)
        scores.append(("cui_bono", cui_bono, 0.25))

        # 4. Synthesis quality
        synthesis = self._score_synthesis(output)
        scores.append(("synthesis", synthesis, 0.25))

        # Weighted average
        total = sum(score * weight for _, score, weight in scores)

        logger.debug(
            "Quality assessment",
            agent=self.task_name,
            scores={name: score for name, score, _ in scores},
            total=total,
        )

        return total

    def _score_confidence_decay(self, output: ChainsOutput) -> float:
        """Check that confidence properly decays across orders."""
        ripple = output.ripple_map

        confidences = [
            ripple.first_order.confidence,
            ripple.second_order.confidence,
            ripple.third_order.confidence,
            ripple.fourth_order.confidence,
        ]

        if ripple.fifth_order:
            confidences.append(ripple.fifth_order.confidence)

        # Check for monotonic decrease (with some tolerance)
        violations = 0
        for i in range(len(confidences) - 1):
            if confidences[i + 1] > confidences[i] + 0.1:  # Allow small increase
                violations += 1

        if violations == 0:
            return 1.0
        elif violations == 1:
            return 0.7
        else:
            return 0.4

    def _score_completeness(self, output: ChainsOutput) -> float:
        """Score chain completeness."""
        ripple = output.ripple_map

        # Check each order has meaningful content
        orders = [
            ripple.first_order,
            ripple.second_order,
            ripple.third_order,
            ripple.fourth_order,
        ]

        complete_count = 0
        for order in orders:
            if (
                len(order.consequences) >= 2
                and all(len(c.description) >= 50 for c in order.consequences)
            ):
                complete_count += 1

        return complete_count / 4.0

    def _score_cui_bono(self, output: ChainsOutput) -> float:
        """Score cui bono analysis depth."""
        cui_bono = output.cui_bono

        indicators = [
            len(cui_bono.obvious_beneficiaries) >= 1,
            len(cui_bono.second_order_beneficiaries) >= 1,
            len(cui_bono.hidden_beneficiaries) >= 1,
            len(cui_bono.key_insight) >= 100,
            any(b.means_to_influence for b in cui_bono.hidden_beneficiaries),
        ]

        return sum(indicators) / len(indicators)

    def _score_synthesis(self, output: ChainsOutput) -> float:
        """Score synthesis quality."""
        synthesis = output.synthesis

        indicators = [
            len(synthesis.most_significant_consequence) >= 100,
            len(synthesis.hidden_game_hypothesis) >= 100,
            len(synthesis.watch_indicators) >= 2,
            len(synthesis.information_gaps) >= 1,
            1 <= synthesis.order_of_significance <= 5,
        ]

        return sum(indicators) / len(indicators)

