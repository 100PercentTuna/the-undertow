"""
Fact Checker Agent.

Verifies factual claims in the analysis against available sources.
"""

from typing import ClassVar, Literal

import structlog
from pydantic import Field

from undertow.agents.base import BaseAgent
from undertow.exceptions import OutputParseError
from undertow.llm.tiers import ModelTier
from undertow.schemas.base import StrictModel

logger = structlog.get_logger()


class FactClaim(StrictModel):
    """A factual claim extracted from analysis."""

    claim_id: str = Field(..., description="Unique claim identifier")
    claim_text: str = Field(..., min_length=10, description="The factual claim")
    source_context: str = Field(..., description="Where in the analysis this appears")
    claim_type: Literal[
        "date_time",
        "statistic",
        "quote",
        "event",
        "relationship",
        "attribution",
    ] = Field(..., description="Type of factual claim")


class VerificationResult(StrictModel):
    """Result of verifying a single claim."""

    claim_id: str = Field(..., description="ID of verified claim")
    verdict: Literal[
        "verified",  # Confirmed by sources
        "unverified",  # Cannot confirm or deny
        "disputed",  # Sources disagree
        "false",  # Contradicted by sources
        "partially_true",  # True with caveats
    ] = Field(..., description="Verification verdict")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in verdict")
    supporting_sources: list[str] = Field(
        default_factory=list,
        description="Sources supporting the claim",
    )
    contradicting_sources: list[str] = Field(
        default_factory=list,
        description="Sources contradicting the claim",
    )
    notes: str = Field(default="", description="Additional notes")
    correction_needed: str | None = Field(
        None,
        description="Suggested correction if claim is false/partially true",
    )


class FactCheckInput(StrictModel):
    """Input for Fact Checker agent."""

    claims: list[FactClaim] = Field(
        ...,
        min_length=1,
        description="Claims to verify",
    )
    available_sources: list[str] = Field(
        default_factory=list,
        description="Source material available for verification",
    )
    analysis_context: str = Field(
        default="",
        description="Context about the analysis being fact-checked",
    )


class FactCheckOutput(StrictModel):
    """Output from Fact Checker agent."""

    results: list[VerificationResult] = Field(
        ...,
        description="Verification results for each claim",
    )
    overall_accuracy_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall accuracy score",
    )
    critical_issues: list[str] = Field(
        default_factory=list,
        description="Critical accuracy issues found",
    )
    verification_coverage: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Proportion of claims that could be verified",
    )
    summary: str = Field(
        ...,
        min_length=50,
        description="Summary of fact-checking results",
    )


FACT_CHECKER_SYSTEM_PROMPT = """You are a meticulous Fact Checker for The Undertow, a world-class geopolitical intelligence publication.

Your role is to verify every factual claim with rigorous standards:

## VERIFICATION STANDARDS

1. **Verify from original sources** - Don't rely on secondary reports
2. **Check dates and numbers precisely** - Small errors undermine credibility
3. **Verify quotes exactly** - Paraphrases must be flagged
4. **Cross-reference when possible** - Multiple sources increase confidence
5. **Note source reliability** - Primary > secondary > tertiary

## VERDICT GUIDELINES

- **verified**: 2+ reliable sources confirm, no contradictions
- **unverified**: Cannot find confirmation either way
- **disputed**: Credible sources disagree
- **false**: Reliable sources directly contradict
- **partially_true**: Core claim true but with important caveats

## CRITICAL ISSUES

Flag as critical if:
- Central claim of the analysis is wrong
- Numbers are off by >10%
- Dates are wrong
- Attribution is incorrect
- Quote is fabricated or significantly altered

Be precise. Our credibility depends on accuracy.

Output as valid JSON matching FactCheckOutput schema."""


class FactCheckerAgent(BaseAgent[FactCheckInput, FactCheckOutput]):
    """
    Fact Checker agent - verifies factual claims.
    
    Uses HIGH tier for careful verification.
    """

    task_name: ClassVar[str] = "fact_checker"
    version: ClassVar[str] = "1.0.0"
    input_schema: ClassVar[type] = FactCheckInput
    output_schema: ClassVar[type] = FactCheckOutput
    default_tier: ClassVar[ModelTier] = ModelTier.HIGH

    def _build_messages(self, input_data: FactCheckInput) -> list[dict[str, str]]:
        """Build messages for fact checker."""
        claims_text = "\n".join(
            f"**[{c.claim_id}]** ({c.claim_type}): {c.claim_text}\n"
            f"  Context: {c.source_context}"
            for c in input_data.claims
        )

        sources_text = ""
        if input_data.available_sources:
            sources_text = "\n\n## AVAILABLE SOURCES\n" + "\n".join(
                f"- {s}" for s in input_data.available_sources
            )

        user_content = f"""## CLAIMS TO VERIFY

{claims_text}
{sources_text}

## ANALYSIS CONTEXT
{input_data.analysis_context or 'General geopolitical analysis'}

## YOUR TASK

Verify each claim. For each:
1. Determine verdict (verified/unverified/disputed/false/partially_true)
2. Provide confidence level
3. List supporting/contradicting sources
4. Note any needed corrections

Then provide:
- Overall accuracy score
- List of critical issues (if any)
- Verification coverage rate
- Summary

Output as valid JSON matching FactCheckOutput schema."""

        return [
            {"role": "system", "content": FACT_CHECKER_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

    def _parse_output(self, content: str) -> FactCheckOutput:
        """Parse fact checker output."""
        try:
            data = self._extract_json(content)
            return FactCheckOutput.model_validate(data)
        except Exception as e:
            logger.error("Failed to parse fact check output", error=str(e))
            raise OutputParseError(
                agent_name=self.task_name,
                error=str(e),
                raw_output=content,
            ) from e

    async def _assess_quality(
        self,
        output: FactCheckOutput,
        input_data: FactCheckInput,
    ) -> float:
        """Assess quality of fact-checking."""
        scores: list[float] = []

        # Coverage: How many claims could be verified?
        scores.append(output.verification_coverage)

        # Specificity: Are verdicts specific enough?
        specific_verdicts = sum(
            1 for r in output.results
            if r.verdict != "unverified" and r.confidence > 0.5
        )
        specificity = specific_verdicts / len(output.results) if output.results else 0
        scores.append(specificity)

        # Source citation
        sourced = sum(
            1 for r in output.results
            if r.supporting_sources or r.contradicting_sources
        )
        source_rate = sourced / len(output.results) if output.results else 0
        scores.append(source_rate)

        return sum(scores) / len(scores)

