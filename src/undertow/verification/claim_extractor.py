"""
Claim extraction and verification.

Extracts verifiable claims from text and verifies them against sources.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, ClassVar
from uuid import UUID

import structlog

from undertow.agents.base import BaseAgent
from undertow.llm.tiers import ModelTier
from undertow.rag.vector_store import get_vector_store, SearchResult
from undertow.schemas.base import StrictModel
from pydantic import Field

logger = structlog.get_logger()


class ClaimType(str, Enum):
    """Types of claims."""

    FACTUAL = "factual"  # Verifiable fact (dates, events, quotes)
    ANALYTICAL = "analytical"  # Interpretation or analysis
    CAUSAL = "causal"  # Causal relationship claim
    PREDICTIVE = "predictive"  # Forward-looking statement
    ATTRIBUTION = "attribution"  # What someone said/did


class VerificationStatus(str, Enum):
    """Verification status for a claim."""

    VERIFIED = "verified"  # Multiple independent sources confirm
    SUPPORTED = "supported"  # At least one reliable source confirms
    UNVERIFIED = "unverified"  # No sources found
    DISPUTED = "disputed"  # Sources contradict each other
    REFUTED = "refuted"  # Evidence contradicts the claim


@dataclass
class ExtractedClaim:
    """A claim extracted from text."""

    claim_id: str
    text: str
    claim_type: ClaimType
    confidence: float
    source_sentence: str
    requires_verification: bool = True


@dataclass
class SourceEvidence:
    """Evidence from a source for/against a claim."""

    source_id: str
    source_url: str | None
    relevant_text: str
    supports: bool  # True = supports, False = contradicts
    confidence: float
    source_reliability: float


@dataclass
class VerifiedClaim:
    """A claim with verification results."""

    claim: ExtractedClaim
    status: VerificationStatus
    evidence: list[SourceEvidence]
    independent_sources: int  # Count of truly independent sources
    verification_score: float  # 0-1 confidence in verification
    notes: str = ""


class ClaimExtractionInput(StrictModel):
    """Input for claim extraction."""

    text: str = Field(..., min_length=50)
    focus_areas: list[str] = Field(
        default_factory=list,
        description="Areas to focus claim extraction on",
    )


class ExtractedClaimSchema(StrictModel):
    """Schema for a single extracted claim."""

    claim_id: str
    text: str = Field(..., min_length=10)
    claim_type: str
    confidence: float = Field(..., ge=0, le=1)
    source_sentence: str
    requires_verification: bool


class ClaimExtractionOutput(StrictModel):
    """Output from claim extraction."""

    claims: list[ExtractedClaimSchema]
    total_claims: int
    verifiable_claims: int


CLAIM_EXTRACTION_PROMPT = """You are a claim extraction specialist for The Undertow, a geopolitical analysis publication.

Your task is to extract VERIFIABLE CLAIMS from the provided text.

## CLAIM TYPES

1. **factual**: Verifiable facts (dates, events, statistics, quotes)
   - "The agreement was signed on January 15, 2025"
   - "The population of X is 50 million"

2. **analytical**: Interpretations requiring evidence
   - "This represents a shift in policy"
   - "The motivation was primarily economic"

3. **causal**: Claims about cause and effect
   - "The sanctions led to economic decline"
   - "This action was in response to..."

4. **predictive**: Forward-looking statements
   - "This will likely result in..."
   - "Expect increased tensions..."

5. **attribution**: What someone said or did
   - "The minister stated that..."
   - "According to official sources..."

## EXTRACTION RULES

1. Extract discrete, specific claims (not vague statements)
2. Mark claims that require verification (factual, causal, attribution)
3. Rate confidence in claim extraction (not claim truth)
4. Include the source sentence for context
5. Prioritize claims central to the argument

## OUTPUT FORMAT

Return JSON array of claims with:
- claim_id: Unique identifier (c1, c2, etc.)
- text: The claim text
- claim_type: One of the types above
- confidence: How confident you are this IS a claim (0-1)
- source_sentence: Original sentence containing the claim
- requires_verification: Whether this claim needs source verification

Focus on claims that are:
1. Central to the analysis
2. Potentially controversial or non-obvious
3. Verifiable against sources"""


class ClaimExtractor(BaseAgent[ClaimExtractionInput, ClaimExtractionOutput]):
    """
    Extracts verifiable claims from text.

    Uses an LLM to identify discrete claims that can be verified
    against sources.
    """

    task_name: ClassVar[str] = "claim_extraction"
    version: ClassVar[str] = "1.0.0"
    input_schema: ClassVar[type] = ClaimExtractionInput
    output_schema: ClassVar[type] = ClaimExtractionOutput
    default_tier: ClassVar[ModelTier] = ModelTier.STANDARD

    def _build_messages(self, input_data: ClaimExtractionInput) -> list[dict[str, str]]:
        """Build messages for claim extraction."""
        focus = ""
        if input_data.focus_areas:
            focus = f"\n\nFocus especially on claims related to: {', '.join(input_data.focus_areas)}"

        return [
            {"role": "system", "content": CLAIM_EXTRACTION_PROMPT},
            {"role": "user", "content": f"Extract claims from:\n\n{input_data.text}{focus}"},
        ]

    def _parse_output(self, content: str) -> ClaimExtractionOutput:
        """Parse extraction output."""
        data = self._extract_json(content)

        # Handle both array and object responses
        if isinstance(data, list):
            claims = data
        else:
            claims = data.get("claims", [])

        return ClaimExtractionOutput(
            claims=[ExtractedClaimSchema(**c) for c in claims],
            total_claims=len(claims),
            verifiable_claims=sum(1 for c in claims if c.get("requires_verification", True)),
        )

    async def _assess_quality(
        self,
        output: ClaimExtractionOutput,
        input_data: ClaimExtractionInput,
    ) -> float:
        """Assess quality of extraction."""
        if output.total_claims == 0:
            return 0.3  # Text might have no claims

        # Score based on claim specificity
        return min(1.0, 0.5 + (output.verifiable_claims / 10) * 0.5)


class ClaimVerifier:
    """
    Verifies extracted claims against sources.

    Uses RAG to find supporting/contradicting evidence.
    """

    def __init__(self) -> None:
        """Initialize verifier."""
        self._vector_store = get_vector_store()

    async def verify_claim(
        self,
        claim: ExtractedClaim,
        zones: list[str] | None = None,
    ) -> VerifiedClaim:
        """
        Verify a single claim against sources.

        Args:
            claim: Claim to verify
            zones: Geographic zones to search within

        Returns:
            VerifiedClaim with verification results
        """
        if not claim.requires_verification:
            return VerifiedClaim(
                claim=claim,
                status=VerificationStatus.UNVERIFIED,
                evidence=[],
                independent_sources=0,
                verification_score=0.5,
                notes="Claim marked as not requiring verification",
            )

        # Search for relevant sources
        search_results = await self._vector_store.hybrid_search(
            query=claim.text,
            limit=10,
            zones=zones,
            rerank=True,
        )

        if not search_results.results:
            return VerifiedClaim(
                claim=claim,
                status=VerificationStatus.UNVERIFIED,
                evidence=[],
                independent_sources=0,
                verification_score=0.3,
                notes="No relevant sources found",
            )

        # Analyze each source for support/contradiction
        evidence = await self._analyze_sources(claim, search_results.results)

        # Determine verification status
        status, score = self._determine_status(evidence)

        # Count independent sources
        independent = self._count_independent_sources(evidence)

        return VerifiedClaim(
            claim=claim,
            status=status,
            evidence=evidence,
            independent_sources=independent,
            verification_score=score,
        )

    async def _analyze_sources(
        self,
        claim: ExtractedClaim,
        sources: list[SearchResult],
    ) -> list[SourceEvidence]:
        """Analyze sources for evidence."""
        evidence = []

        for source in sources:
            # Simple heuristic: check for term overlap and sentiment
            # TODO: Use LLM for more sophisticated analysis
            claim_terms = set(claim.text.lower().split())
            source_terms = set(source.content.lower().split())

            overlap = len(claim_terms & source_terms) / len(claim_terms) if claim_terms else 0

            # For now, assume supporting if high overlap
            supports = overlap > 0.3

            evidence.append(
                SourceEvidence(
                    source_id=str(source.id),
                    source_url=source.source_url,
                    relevant_text=source.content[:500],
                    supports=supports,
                    confidence=min(0.9, overlap + 0.2),
                    source_reliability=source.score,
                )
            )

        return evidence

    def _determine_status(
        self,
        evidence: list[SourceEvidence],
    ) -> tuple[VerificationStatus, float]:
        """Determine verification status from evidence."""
        if not evidence:
            return VerificationStatus.UNVERIFIED, 0.3

        supporting = [e for e in evidence if e.supports]
        contradicting = [e for e in evidence if not e.supports]

        if len(supporting) >= 2 and not contradicting:
            return VerificationStatus.VERIFIED, 0.9
        elif len(supporting) >= 1 and not contradicting:
            return VerificationStatus.SUPPORTED, 0.7
        elif contradicting and supporting:
            return VerificationStatus.DISPUTED, 0.5
        elif contradicting and not supporting:
            return VerificationStatus.REFUTED, 0.8
        else:
            return VerificationStatus.UNVERIFIED, 0.3

    def _count_independent_sources(self, evidence: list[SourceEvidence]) -> int:
        """Count independent sources (different domains)."""
        domains = set()

        for e in evidence:
            if e.source_url:
                # Extract domain
                try:
                    from urllib.parse import urlparse
                    domain = urlparse(e.source_url).netloc
                    domains.add(domain)
                except Exception:
                    pass

        return len(domains)

    async def verify_claims_batch(
        self,
        claims: list[ExtractedClaim],
        zones: list[str] | None = None,
    ) -> list[VerifiedClaim]:
        """Verify multiple claims."""
        results = []
        for claim in claims:
            result = await self.verify_claim(claim, zones)
            results.append(result)
        return results


def get_claim_extractor(router: Any) -> ClaimExtractor:
    """Get claim extractor instance."""
    return ClaimExtractor(router)


def get_claim_verifier() -> ClaimVerifier:
    """Get claim verifier instance."""
    return ClaimVerifier()

