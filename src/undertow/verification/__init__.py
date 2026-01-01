"""
Verification module for The Undertow.

Provides claim extraction and verification against sources.
"""

from undertow.verification.claim_extractor import (
    ClaimExtractor,
    ClaimExtractionInput,
    ClaimExtractionOutput,
    ExtractedClaim,
    ClaimType,
    ClaimVerifier,
    VerifiedClaim,
    VerificationStatus,
)

# Singleton instances
_claim_extractor: ClaimExtractor | None = None
_claim_verifier: ClaimVerifier | None = None


def get_claim_extractor(router=None) -> ClaimExtractor:
    """Get or create the claim extractor instance."""
    global _claim_extractor
    if _claim_extractor is None:
        if router is None:
            from undertow.llm.router import get_router
            router = get_router()
        _claim_extractor = ClaimExtractor(router=router)
    return _claim_extractor


def get_claim_verifier() -> ClaimVerifier:
    """Get or create the claim verifier instance."""
    global _claim_verifier
    if _claim_verifier is None:
        _claim_verifier = ClaimVerifier()
    return _claim_verifier


__all__ = [
    # Classes
    "ClaimExtractor",
    "ClaimExtractionInput",
    "ClaimExtractionOutput",
    "ExtractedClaim",
    "ClaimType",
    "ClaimVerifier",
    "VerifiedClaim",
    "VerificationStatus",
    # Factory functions
    "get_claim_extractor",
    "get_claim_verifier",
]
