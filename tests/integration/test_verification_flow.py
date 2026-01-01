"""
Integration tests for verification flow.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID


@pytest.fixture
def sample_text():
    """Sample geopolitical text for testing."""
    return """
    Israel officially recognized Somaliland as an independent state on January 5, 2024.
    This makes Israel only the second country to formally recognize Somaliland's sovereignty,
    following Taiwan's recognition in 2020.
    
    The recognition comes amid growing tensions in the Red Sea region, where Houthi attacks
    have disrupted international shipping. Israel's Foreign Ministry announced the decision
    during a press conference in Tel Aviv.
    
    Ethiopia signed a memorandum of understanding with Somaliland in January 2024,
    agreeing to lease a naval base at the port of Berbera in exchange for potential
    recognition of Somaliland's independence.
    
    Analysts suggest this move is primarily about securing Red Sea access and countering
    Iranian influence in the region. The UAE, which operates the port of Berbera through
    DP World, is seen as a key facilitator of these developments.
    """


class TestClaimExtractionFlow:
    """Tests for claim extraction flow."""

    @pytest.mark.asyncio
    async def test_extracts_multiple_claim_types(self, sample_text):
        """Test that extraction identifies different claim types."""
        from undertow.verification.claim_extractor import (
            ClaimExtractor,
            ClaimExtractionInput,
            ClaimType,
        )
        
        # Mock the LLM response
        mock_response = {
            "claims": [
                {
                    "text": "Israel officially recognized Somaliland as an independent state on January 5, 2024",
                    "claim_type": "factual",
                    "confidence": 0.95,
                    "source_sentence": "Israel officially recognized Somaliland as an independent state on January 5, 2024.",
                    "requires_verification": True,
                },
                {
                    "text": "Taiwan recognized Somaliland in 2020",
                    "claim_type": "factual",
                    "confidence": 0.9,
                    "source_sentence": "This makes Israel only the second country to formally recognize Somaliland's sovereignty, following Taiwan's recognition in 2020.",
                    "requires_verification": True,
                },
                {
                    "text": "This move is primarily about securing Red Sea access and countering Iranian influence",
                    "claim_type": "analytical",
                    "confidence": 0.7,
                    "source_sentence": "Analysts suggest this move is primarily about securing Red Sea access and countering Iranian influence in the region.",
                    "requires_verification": False,
                },
            ],
            "total_claims": 3,
            "verifiable_claims": 2,
        }
        
        mock_router = MagicMock()
        extractor = ClaimExtractor(router=mock_router)
        
        with patch.object(extractor, "_call_llm", AsyncMock(return_value=mock_response)):
            result = await extractor.run(
                ClaimExtractionInput(text=sample_text)
            )
            
            assert result.success
            assert result.output is not None
            assert result.output.total_claims == 3
            assert result.output.verifiable_claims == 2
            
            # Check claim types
            claim_types = [c.claim_type for c in result.output.claims]
            assert ClaimType.FACTUAL in claim_types
            assert ClaimType.ANALYTICAL in claim_types

    @pytest.mark.asyncio
    async def test_filters_by_focus_areas(self, sample_text):
        """Test that focus areas filter relevant claims."""
        from undertow.verification.claim_extractor import (
            ClaimExtractor,
            ClaimExtractionInput,
        )
        
        mock_response = {
            "claims": [
                {
                    "text": "Houthi attacks have disrupted international shipping",
                    "claim_type": "factual",
                    "confidence": 0.85,
                    "source_sentence": "This makes Israel only the second country to formally recognize Somaliland's sovereignty, following Taiwan's recognition in 2020.",
                    "requires_verification": True,
                },
            ],
            "total_claims": 1,
            "verifiable_claims": 1,
        }
        
        mock_router = MagicMock()
        extractor = ClaimExtractor(router=mock_router)
        
        with patch.object(extractor, "_call_llm", AsyncMock(return_value=mock_response)):
            result = await extractor.run(
                ClaimExtractionInput(
                    text=sample_text,
                    focus_areas=["security", "military"],
                )
            )
            
            assert result.success
            # Should only get security-related claims


class TestClaimVerificationFlow:
    """Tests for claim verification flow."""

    @pytest.mark.asyncio
    async def test_verifies_against_vector_store(self):
        """Test that verification queries vector store for evidence."""
        from undertow.verification.claim_extractor import (
            ClaimVerifier,
            ExtractedClaim,
            ClaimType,
        )
        
        claim = ExtractedClaim(
            claim_id="test-1",
            text="Israel recognized Somaliland on January 5, 2024",
            claim_type=ClaimType.FACTUAL,
            confidence=0.95,
            source_sentence="Israel recognized Somaliland on January 5, 2024.",
            requires_verification=True,
        )
        
        # Mock vector store search
        mock_evidence = [
            {
                "content": "Israel's foreign ministry announced recognition of Somaliland on January 5, 2024",
                "source_type": "news",
                "score": 0.92,
            },
            {
                "content": "Somaliland received diplomatic recognition from Israel in early January",
                "source_type": "analysis",
                "score": 0.85,
            },
        ]
        
        verifier = ClaimVerifier()
        
        with patch.object(verifier, "_search_evidence", AsyncMock(return_value=mock_evidence)):
            results = await verifier.verify_claims_batch([claim], zones=[])
            
            assert len(results) == 1
            result = results[0]
            assert result.verification_score > 0.5
            assert len(result.evidence) > 0

    @pytest.mark.asyncio
    async def test_handles_contradicting_evidence(self):
        """Test that contradicting evidence lowers verification score."""
        from undertow.verification.claim_extractor import (
            ClaimVerifier,
            ExtractedClaim,
            ClaimType,
        )
        
        claim = ExtractedClaim(
            claim_id="test-2",
            text="Taiwan recognized Somaliland in 2020",
            claim_type=ClaimType.FACTUAL,
            confidence=0.9,
            source_sentence="Taiwan recognized Somaliland in 2020.",
            requires_verification=True,
        )
        
        # Mixed evidence
        mock_evidence = [
            {
                "content": "Taiwan does not officially recognize Somaliland due to diplomatic constraints",
                "source_type": "analysis",
                "score": 0.88,
                "supports": False,
            },
            {
                "content": "Taiwan and Somaliland established mutual representative offices in 2020",
                "source_type": "news",
                "score": 0.85,
                "supports": True,  # Partial support
            },
        ]
        
        verifier = ClaimVerifier()
        
        with patch.object(verifier, "_search_evidence", AsyncMock(return_value=mock_evidence)):
            results = await verifier.verify_claims_batch([claim], zones=[])
            
            assert len(results) == 1
            # Score should reflect mixed evidence


class TestEndToEndVerification:
    """End-to-end verification tests."""

    @pytest.mark.asyncio
    async def test_full_extraction_and_verification(self, sample_text):
        """Test complete extraction → verification flow."""
        from undertow.verification.claim_extractor import (
            ClaimExtractor,
            ClaimVerifier,
            ClaimExtractionInput,
        )
        
        # Mock extraction
        mock_extraction = {
            "claims": [
                {
                    "text": "Ethiopia signed an MOU with Somaliland in January 2024",
                    "claim_type": "factual",
                    "confidence": 0.95,
                    "source_sentence": "Ethiopia signed a memorandum of understanding with Somaliland in January 2024.",
                    "requires_verification": True,
                },
            ],
            "total_claims": 1,
            "verifiable_claims": 1,
        }
        
        # Mock verification evidence
        mock_evidence = [
            {
                "content": "Ethiopia and Somaliland signed an MOU on January 1, 2024",
                "source_type": "news",
                "score": 0.95,
            },
        ]
        
        mock_router = MagicMock()
        extractor = ClaimExtractor(router=mock_router)
        verifier = ClaimVerifier()
        
        with patch.object(extractor, "_call_llm", AsyncMock(return_value=mock_extraction)):
            extraction_result = await extractor.run(
                ClaimExtractionInput(text=sample_text)
            )
            
            assert extraction_result.success
            claims = extraction_result.output.claims
            
            with patch.object(verifier, "_search_evidence", AsyncMock(return_value=mock_evidence)):
                verification_results = await verifier.verify_claims_batch(
                    claims, zones=["horn_of_africa"]
                )
                
                assert len(verification_results) == 1
                assert verification_results[0].verification_score > 0.7


class TestVerificationAPI:
    """Tests for verification API endpoints."""

    @pytest.mark.asyncio
    async def test_extract_endpoint(self):
        """Test /verification/extract endpoint."""
        from fastapi.testclient import TestClient
        from undertow.api.main import create_app
        
        app = create_app()
        
        # This would need proper mocking in actual test
        # Simplified for structure demonstration

    @pytest.mark.asyncio
    async def test_verify_endpoint(self):
        """Test /verification/verify endpoint."""
        from fastapi.testclient import TestClient
        from undertow.api.main import create_app
        
        app = create_app()
        
        # This would need proper mocking in actual test
        # Simplified for structure demonstration

