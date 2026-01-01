"""
Verification API routes.

Provides endpoints for claim extraction and verification.
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from undertow.verification import (
    get_claim_extractor,
    get_claim_verifier,
    VerificationStatus,
)
from undertow.verification.claim_extractor import (
    ClaimExtractionInput,
    ExtractedClaim,
    ClaimType,
)
from undertow.llm.router import get_router

router = APIRouter(prefix="/verification", tags=["Verification"])


class ExtractClaimsRequest(BaseModel):
    """Request to extract claims from text."""

    text: str = Field(..., min_length=50)
    focus_areas: list[str] = Field(default_factory=list)


class ExtractedClaimResponse(BaseModel):
    """Response for a single extracted claim."""

    claim_id: str
    text: str
    claim_type: str
    confidence: float
    source_sentence: str
    requires_verification: bool


class ExtractClaimsResponse(BaseModel):
    """Response for claim extraction."""

    claims: list[ExtractedClaimResponse]
    total_claims: int
    verifiable_claims: int


class VerifyClaimsRequest(BaseModel):
    """Request to verify claims."""

    claims: list[ExtractedClaimResponse]
    zones: list[str] = Field(default_factory=list)


class VerifiedClaimResponse(BaseModel):
    """Response for a verified claim."""

    claim_id: str
    claim_text: str
    status: str
    verification_score: float
    independent_sources: int
    evidence_count: int


class VerifyClaimsResponse(BaseModel):
    """Response for claim verification."""

    verified_claims: list[VerifiedClaimResponse]
    total_verified: int
    total_supported: int
    total_disputed: int
    total_refuted: int


@router.post("/extract", response_model=ExtractClaimsResponse)
async def extract_claims(request: ExtractClaimsRequest) -> ExtractClaimsResponse:
    """
    Extract verifiable claims from text.

    Uses LLM to identify discrete claims that can be verified against sources.
    """
    router_instance = get_router()
    extractor = get_claim_extractor(router_instance)

    result = await extractor.run(
        ClaimExtractionInput(
            text=request.text,
            focus_areas=request.focus_areas,
        )
    )

    if not result.success or not result.output:
        raise HTTPException(status_code=500, detail="Claim extraction failed")

    claims = [
        ExtractedClaimResponse(
            claim_id=c.claim_id,
            text=c.text,
            claim_type=c.claim_type,
            confidence=c.confidence,
            source_sentence=c.source_sentence,
            requires_verification=c.requires_verification,
        )
        for c in result.output.claims
    ]

    return ExtractClaimsResponse(
        claims=claims,
        total_claims=result.output.total_claims,
        verifiable_claims=result.output.verifiable_claims,
    )


@router.post("/verify", response_model=VerifyClaimsResponse)
async def verify_claims(request: VerifyClaimsRequest) -> VerifyClaimsResponse:
    """
    Verify claims against sources.

    Searches vector store for supporting/contradicting evidence.
    """
    verifier = get_claim_verifier()

    # Convert to ExtractedClaim objects
    claims = [
        ExtractedClaim(
            claim_id=c.claim_id,
            text=c.text,
            claim_type=ClaimType(c.claim_type) if c.claim_type in [e.value for e in ClaimType] else ClaimType.FACTUAL,
            confidence=c.confidence,
            source_sentence=c.source_sentence,
            requires_verification=c.requires_verification,
        )
        for c in request.claims
    ]

    # Verify all claims
    verified = await verifier.verify_claims_batch(claims, request.zones)

    # Build response
    responses = [
        VerifiedClaimResponse(
            claim_id=v.claim.claim_id,
            claim_text=v.claim.text,
            status=v.status.value,
            verification_score=v.verification_score,
            independent_sources=v.independent_sources,
            evidence_count=len(v.evidence),
        )
        for v in verified
    ]

    return VerifyClaimsResponse(
        verified_claims=responses,
        total_verified=sum(1 for v in verified if v.status == VerificationStatus.VERIFIED),
        total_supported=sum(1 for v in verified if v.status == VerificationStatus.SUPPORTED),
        total_disputed=sum(1 for v in verified if v.status == VerificationStatus.DISPUTED),
        total_refuted=sum(1 for v in verified if v.status == VerificationStatus.REFUTED),
    )


@router.post("/extract-and-verify")
async def extract_and_verify(
    text: str = Field(..., min_length=50),
    zones: list[str] = Field(default_factory=list),
) -> dict[str, Any]:
    """
    Combined endpoint: extract claims and verify them.
    """
    # Extract
    extract_response = await extract_claims(
        ExtractClaimsRequest(text=text, focus_areas=[])
    )

    if not extract_response.claims:
        return {
            "claims_extracted": 0,
            "claims_verified": 0,
            "verification_score": 1.0,
            "details": [],
        }

    # Verify
    verify_response = await verify_claims(
        VerifyClaimsRequest(claims=extract_response.claims, zones=zones)
    )

    # Calculate overall score
    if verify_response.verified_claims:
        avg_score = sum(c.verification_score for c in verify_response.verified_claims) / len(verify_response.verified_claims)
    else:
        avg_score = 0.5

    return {
        "claims_extracted": extract_response.total_claims,
        "claims_verified": verify_response.total_verified + verify_response.total_supported,
        "claims_disputed": verify_response.total_disputed,
        "claims_refuted": verify_response.total_refuted,
        "verification_score": avg_score,
        "details": [c.model_dump() for c in verify_response.verified_claims],
    }

