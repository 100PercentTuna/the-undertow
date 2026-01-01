"""
Debate agents: Challenger, Advocate, Judge.

These form the adversarial review protocol.
"""

from typing import ClassVar

import structlog

from undertow.agents.base import BaseAgent
from undertow.exceptions import OutputParseError
from undertow.llm.tiers import ModelTier
from undertow.schemas.agents.debate import (
    ChallengerInput,
    ChallengerOutput,
    AdvocateInput,
    AdvocateOutput,
    JudgeInput,
    JudgeOutput,
    DebateChallenge,
    AdvocateResponse,
    JudgeRuling,
)

logger = structlog.get_logger()


# =============================================================================
# CHALLENGER AGENT
# =============================================================================

CHALLENGER_SYSTEM_PROMPT = """You are the Challenger in The Undertow's adversarial review protocol.

Your role is to FIND WEAKNESSES in geopolitical analysis. Be rigorous but fair.

## CHALLENGE TYPES

1. **factual_accuracy**: Claim may be factually incorrect or unverified
2. **logical_flaw**: Reasoning doesn't follow
3. **missing_evidence**: Claim lacks sufficient support
4. **alternative_explanation**: Plausible alternative not considered
5. **overconfidence**: Confidence higher than evidence warrants
6. **bias_detected**: Systematic bias apparent
7. **causal_gap**: Missing link in causal chain
8. **source_reliability**: Source may not be reliable

## SEVERITY LEVELS

- **low**: Minor issue, could be improved
- **medium**: Should be addressed
- **high**: Significantly weakens analysis
- **critical**: Fundamental flaw

## RULES

1. Challenge substantively, not pedantically
2. Don't challenge well-supported claims
3. Identify 2-5 challenges per review
4. Be specific - cite the exact claim
5. Explain WHY it's a problem
6. Suggest what evidence would help

Output as valid JSON matching ChallengerOutput schema."""


class ChallengerAgent(BaseAgent[ChallengerInput, ChallengerOutput]):
    """
    Challenger agent - identifies weaknesses in analysis.

    Uses FRONTIER tier for thorough critique.
    """

    task_name: ClassVar[str] = "challenger"
    version: ClassVar[str] = "1.0.0"
    input_schema: ClassVar[type] = ChallengerInput
    output_schema: ClassVar[type] = ChallengerOutput
    default_tier: ClassVar[ModelTier] = ModelTier.FRONTIER

    def _build_messages(self, input_data: ChallengerInput) -> list[dict[str, str]]:
        """Build messages for challenger."""
        prior_text = ""
        if input_data.prior_challenges:
            prior_text = "\n\n## PRIOR CHALLENGES (don't repeat)\n" + "\n".join(
                f"- {c.target_claim[:50]}..." for c in input_data.prior_challenges
            )

        motivation_text = ""
        if input_data.motivation_synthesis:
            motivation_text = f"\n\n## MOTIVATION ANALYSIS\n{input_data.motivation_synthesis}"

        chains_text = ""
        if input_data.chains_synthesis:
            chains_text = f"\n\n## CHAINS ANALYSIS\n{input_data.chains_synthesis}"

        claims_text = "\n".join(f"- {c}" for c in input_data.key_claims)

        user_content = f"""## ANALYSIS SUMMARY

{input_data.analysis_summary}
{motivation_text}
{chains_text}

## KEY CLAIMS TO SCRUTINIZE

{claims_text}
{prior_text}

## YOUR TASK

Identify weaknesses. Be rigorous but fair. Output JSON matching ChallengerOutput."""

        return [
            {"role": "system", "content": CHALLENGER_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

    def _parse_output(self, content: str) -> ChallengerOutput:
        """Parse challenger output."""
        try:
            data = self._extract_json(content)
            return ChallengerOutput.model_validate(data)
        except Exception as e:
            logger.error("Failed to parse challenger output", error=str(e))
            raise OutputParseError(
                agent_name=self.task_name,
                error=str(e),
                raw_output=content,
            ) from e

    async def _assess_quality(
        self,
        output: ChallengerOutput,
        input_data: ChallengerInput,
    ) -> float:
        """Assess quality of challenges."""
        scores: list[float] = []

        # Did we generate challenges?
        if output.challenges:
            scores.append(min(1.0, len(output.challenges) / 3))
        else:
            scores.append(0.3)

        # Are challenges substantive?
        for challenge in output.challenges:
            if len(challenge.challenge_text) >= 100:
                scores.append(1.0)
            elif len(challenge.challenge_text) >= 50:
                scores.append(0.7)
            else:
                scores.append(0.4)

        return sum(scores) / max(len(scores), 1)


# =============================================================================
# ADVOCATE AGENT
# =============================================================================

ADVOCATE_SYSTEM_PROMPT = """You are the Advocate in The Undertow's adversarial review protocol.

Your role is to DEFEND the analysis against challenges - but honestly.

## RESPONSE TYPES

1. **defend**: The challenge is wrong, analysis stands
2. **acknowledge**: The challenge has merit, issue was known
3. **partial_concede**: Partially valid, suggest modification
4. **full_concede**: Challenge is correct, revision needed

## RULES

1. Defend ONLY where defensible
2. Concede when the challenge has merit
3. Provide evidence for defenses
4. Suggest specific modifications when needed
5. Never be defensive for its own sake
6. Intellectual honesty > winning

## GOOD DEFENSES

- Cite specific evidence
- Show the reasoning was sound
- Demonstrate alternative was considered
- Explain why confidence was appropriate

## WHEN TO CONCEDE

- Challenge identifies real gap
- Evidence is insufficient
- Alternative is equally plausible
- Source reliability is questionable

Output as valid JSON matching AdvocateOutput schema."""


class AdvocateAgent(BaseAgent[AdvocateInput, AdvocateOutput]):
    """
    Advocate agent - defends analysis against challenges.

    Uses HIGH tier for nuanced defense.
    """

    task_name: ClassVar[str] = "advocate"
    version: ClassVar[str] = "1.0.0"
    input_schema: ClassVar[type] = AdvocateInput
    output_schema: ClassVar[type] = AdvocateOutput
    default_tier: ClassVar[ModelTier] = ModelTier.HIGH

    def _build_messages(self, input_data: AdvocateInput) -> list[dict[str, str]]:
        """Build messages for advocate."""
        evidence_text = ""
        if input_data.available_evidence:
            evidence_text = "\n\n## AVAILABLE EVIDENCE\n" + "\n".join(
                f"- {e}" for e in input_data.available_evidence
            )

        user_content = f"""## ORIGINAL ANALYSIS

{input_data.original_analysis}

## CHALLENGE TO ADDRESS

**Type**: {input_data.challenge.challenge_type}
**Severity**: {input_data.challenge.severity}
**Target Claim**: {input_data.challenge.target_claim}

**Challenge**: {input_data.challenge.challenge_text}

**Evidence Requested**: {', '.join(input_data.challenge.evidence_requested) or 'None specified'}
{evidence_text}

## YOUR TASK

Respond to this challenge. Defend if defensible, concede if warranted.
Output JSON matching AdvocateOutput."""

        return [
            {"role": "system", "content": ADVOCATE_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

    def _parse_output(self, content: str) -> AdvocateOutput:
        """Parse advocate output."""
        try:
            data = self._extract_json(content)
            return AdvocateOutput.model_validate(data)
        except Exception as e:
            logger.error("Failed to parse advocate output", error=str(e))
            raise OutputParseError(
                agent_name=self.task_name,
                error=str(e),
                raw_output=content,
            ) from e

    async def _assess_quality(
        self,
        output: AdvocateOutput,
        input_data: AdvocateInput,
    ) -> float:
        """Assess quality of response."""
        scores: list[float] = []

        # Is response substantive?
        if len(output.response.response_text) >= 100:
            scores.append(1.0)
        elif len(output.response.response_text) >= 50:
            scores.append(0.7)
        else:
            scores.append(0.4)

        # Did we provide evidence for defenses?
        if output.response.response_type == "defend":
            if output.response.evidence_provided:
                scores.append(1.0)
            else:
                scores.append(0.5)

        # Did we suggest modification when conceding?
        if output.response.response_type in ["partial_concede", "full_concede"]:
            if output.response.suggested_modification:
                scores.append(1.0)
            else:
                scores.append(0.6)

        return sum(scores) / max(len(scores), 1)


# =============================================================================
# JUDGE AGENT
# =============================================================================

JUDGE_SYSTEM_PROMPT = """You are the Judge in The Undertow's adversarial review protocol.

Your role is to RULE on challenge-response exchanges IMPARTIALLY.

## RULINGS

1. **challenge_sustained**: Challenge wins, revision needed
2. **challenge_overruled**: Defense wins, analysis stands
3. **partial_sustain**: Both have merit, minor adjustment

## REQUIRED ACTIONS

- **no_change**: Analysis is fine
- **minor_revision**: Small adjustment needed
- **significant_revision**: Substantial rewrite needed
- **remove_claim**: Claim should be removed entirely

## JUDGING CRITERIA

1. **Evidence Quality**: Is the defense evidence-based?
2. **Logical Soundness**: Does the reasoning hold?
3. **Proportionality**: Is the challenge warranted?
4. **Intellectual Honesty**: Is either side being evasive?

## RULES

1. Be impartial - no bias toward either side
2. Focus on substance, not rhetoric
3. Explain your reasoning clearly
4. Be specific about required actions
5. Err on side of caution for high-stakes claims

Output as valid JSON matching JudgeOutput schema."""


class JudgeAgent(BaseAgent[JudgeInput, JudgeOutput]):
    """
    Judge agent - rules on challenge-response exchanges.

    Uses FRONTIER tier for authoritative judgment.
    """

    task_name: ClassVar[str] = "judge"
    version: ClassVar[str] = "1.0.0"
    input_schema: ClassVar[type] = JudgeInput
    output_schema: ClassVar[type] = JudgeOutput
    default_tier: ClassVar[ModelTier] = ModelTier.FRONTIER

    def _build_messages(self, input_data: JudgeInput) -> list[dict[str, str]]:
        """Build messages for judge."""
        context_text = ""
        if input_data.context:
            context_text = f"\n\n## CONTEXT\n{input_data.context}"

        user_content = f"""## THE DISPUTE

**Original Claim**: {input_data.original_claim}

### CHALLENGE

**Type**: {input_data.challenge.challenge_type}
**Severity**: {input_data.challenge.severity}
**Challenge**: {input_data.challenge.challenge_text}

### RESPONSE

**Type**: {input_data.response.response_type}
**Response**: {input_data.response.response_text}
**Evidence**: {', '.join(input_data.response.evidence_provided) or 'None'}
**Suggested Modification**: {input_data.response.suggested_modification or 'None'}
{context_text}

## YOUR TASK

Rule on this exchange. Be impartial. Output JSON matching JudgeOutput."""

        return [
            {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

    def _parse_output(self, content: str) -> JudgeOutput:
        """Parse judge output."""
        try:
            data = self._extract_json(content)
            return JudgeOutput.model_validate(data)
        except Exception as e:
            logger.error("Failed to parse judge output", error=str(e))
            raise OutputParseError(
                agent_name=self.task_name,
                error=str(e),
                raw_output=content,
            ) from e

    async def _assess_quality(
        self,
        output: JudgeOutput,
        input_data: JudgeInput,
    ) -> float:
        """Assess quality of ruling."""
        scores: list[float] = []

        # Is reasoning substantive?
        if len(output.ruling.reasoning) >= 100:
            scores.append(1.0)
        elif len(output.ruling.reasoning) >= 50:
            scores.append(0.7)
        else:
            scores.append(0.4)

        # Is confidence reasonable?
        if 0.6 <= output.confidence_in_ruling <= 0.95:
            scores.append(1.0)
        elif output.confidence_in_ruling > 0.95:
            scores.append(0.7)  # Overconfident
        else:
            scores.append(0.6)  # Underconfident

        # Are action details provided when needed?
        if output.ruling.required_action != "no_change":
            if output.ruling.action_details:
                scores.append(1.0)
            else:
                scores.append(0.5)

        return sum(scores) / max(len(scores), 1)
