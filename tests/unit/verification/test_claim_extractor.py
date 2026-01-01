"""
Unit tests for claim extraction.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from undertow.verification.claim_extractor import (
    ClaimExtractor,
    ClaimExtractionInput,
    ClaimExtractionOutput,
    ExtractedClaim,
    ClaimType,
)


@pytest.fixture
def mock_router():
    """Create mock LLM router."""
    router = MagicMock()
    router.get_provider = MagicMock(return_value=MagicMock())
    return router


@pytest.fixture
def claim_extractor(mock_router):
    """Create claim extractor with mocked router."""
    return ClaimExtractor(router=mock_router)


class TestClaimExtractor:
    """Tests for ClaimExtractor agent."""

    @pytest.mark.asyncio
    async def test_extracts_factual_claims(self, claim_extractor, mock_router):
        """Test extracting factual claims from text."""
        text = """
        Israel recognized Somaliland as an independent state on February 1, 2024.
        This makes Israel the first country to formally recognize Somaliland's
        independence since it declared independence from Somalia in 1991.
        The recognition comes after months of diplomatic negotiations.
        """
        
        # Mock LLM response
        mock_response = {
            "claims": [
                {
                    "text": "Israel recognized Somaliland as an independent state on February 1, 2024",
                    "claim_type": "factual",
                    "confidence": 0.95,
                    "source_sentence": "Israel recognized Somaliland as an independent state on February 1, 2024.",
                    "requires_verification": True,
                },
                {
                    "text": "Israel is the first country to formally recognize Somaliland's independence",
                    "claim_type": "factual",
                    "confidence": 0.9,
                    "source_sentence": "This makes Israel the first country to formally recognize Somaliland's independence since it declared independence from Somalia in 1991.",
                    "requires_verification": True,
                },
            ],
            "total_claims": 2,
            "verifiable_claims": 2,
        }
        
        with patch.object(claim_extractor, "_call_llm", AsyncMock(return_value=mock_response)):
            result = await claim_extractor.run(
                ClaimExtractionInput(text=text)
            )
            
            assert result.success
            assert result.output is not None
            assert result.output.total_claims == 2
            assert len(result.output.claims) == 2
            assert result.output.claims[0].claim_type == ClaimType.FACTUAL

    @pytest.mark.asyncio
    async def test_identifies_analytical_claims(self, claim_extractor):
        """Test identifying analytical/interpretive claims."""
        text = """
        The recognition likely signals Israel's strategic interest in the
        Red Sea corridor. This move appears designed to counter Iranian
        influence in the region.
        """
        
        mock_response = {
            "claims": [
                {
                    "text": "The recognition signals Israel's strategic interest in the Red Sea corridor",
                    "claim_type": "analytical",
                    "confidence": 0.7,
                    "source_sentence": "The recognition likely signals Israel's strategic interest in the Red Sea corridor.",
                    "requires_verification": False,
                },
            ],
            "total_claims": 1,
            "verifiable_claims": 0,
        }
        
        with patch.object(claim_extractor, "_call_llm", AsyncMock(return_value=mock_response)):
            result = await claim_extractor.run(
                ClaimExtractionInput(text=text)
            )
            
            assert result.success
            assert result.output.claims[0].claim_type == ClaimType.ANALYTICAL
            assert not result.output.claims[0].requires_verification

    @pytest.mark.asyncio
    async def test_handles_empty_text(self, claim_extractor):
        """Test handling empty text gracefully."""
        with pytest.raises(ValueError):
            await claim_extractor.run(
                ClaimExtractionInput(text="")
            )

    @pytest.mark.asyncio
    async def test_assigns_unique_claim_ids(self, claim_extractor):
        """Test that each claim gets a unique ID."""
        mock_response = {
            "claims": [
                {
                    "text": "Claim 1",
                    "claim_type": "factual",
                    "confidence": 0.9,
                    "source_sentence": "Claim 1.",
                    "requires_verification": True,
                },
                {
                    "text": "Claim 2",
                    "claim_type": "factual",
                    "confidence": 0.9,
                    "source_sentence": "Claim 2.",
                    "requires_verification": True,
                },
            ],
            "total_claims": 2,
            "verifiable_claims": 2,
        }
        
        with patch.object(claim_extractor, "_call_llm", AsyncMock(return_value=mock_response)):
            result = await claim_extractor.run(
                ClaimExtractionInput(text="Some text with claims")
            )
            
            claim_ids = [c.claim_id for c in result.output.claims]
            assert len(claim_ids) == len(set(claim_ids))  # All unique

    @pytest.mark.asyncio
    async def test_filters_by_focus_areas(self, claim_extractor):
        """Test filtering claims by focus areas."""
        text = """
        The economy grew by 5% last quarter.
        Military forces conducted exercises near the border.
        A new trade agreement was signed.
        """
        
        mock_response = {
            "claims": [
                {
                    "text": "Military forces conducted exercises near the border",
                    "claim_type": "factual",
                    "confidence": 0.95,
                    "source_sentence": "Military forces conducted exercises near the border.",
                    "requires_verification": True,
                },
            ],
            "total_claims": 1,
            "verifiable_claims": 1,
        }
        
        with patch.object(claim_extractor, "_call_llm", AsyncMock(return_value=mock_response)):
            result = await claim_extractor.run(
                ClaimExtractionInput(
                    text=text,
                    focus_areas=["military", "security"],
                )
            )
            
            # Should only extract military-related claims
            assert result.output.total_claims == 1


class TestExtractedClaim:
    """Tests for ExtractedClaim model."""

    def test_claim_creation(self):
        """Test creating an extracted claim."""
        claim = ExtractedClaim(
            claim_id="test-001",
            text="Israel recognized Somaliland",
            claim_type=ClaimType.FACTUAL,
            confidence=0.95,
            source_sentence="Israel recognized Somaliland on February 1.",
            requires_verification=True,
        )
        
        assert claim.claim_id == "test-001"
        assert claim.claim_type == ClaimType.FACTUAL
        assert claim.confidence == 0.95
        assert claim.requires_verification

    def test_claim_type_enum(self):
        """Test claim type enumeration."""
        assert ClaimType.FACTUAL.value == "factual"
        assert ClaimType.ANALYTICAL.value == "analytical"
        assert ClaimType.PREDICTIVE.value == "predictive"
        assert ClaimType.ATTRIBUTIVE.value == "attributive"


class TestClaimExtractionInput:
    """Tests for ClaimExtractionInput model."""

    def test_input_creation(self):
        """Test creating extraction input."""
        input_data = ClaimExtractionInput(
            text="Test text",
            focus_areas=["security", "diplomacy"],
        )
        
        assert input_data.text == "Test text"
        assert "security" in input_data.focus_areas

    def test_input_without_focus_areas(self):
        """Test input without focus areas defaults to empty list."""
        input_data = ClaimExtractionInput(text="Test text")
        
        assert input_data.focus_areas == []


class TestClaimExtractionOutput:
    """Tests for ClaimExtractionOutput model."""

    def test_output_creation(self):
        """Test creating extraction output."""
        output = ClaimExtractionOutput(
            claims=[
                ExtractedClaim(
                    claim_id="1",
                    text="Test claim",
                    claim_type=ClaimType.FACTUAL,
                    confidence=0.9,
                    source_sentence="Test claim.",
                    requires_verification=True,
                )
            ],
            total_claims=1,
            verifiable_claims=1,
        )
        
        assert output.total_claims == 1
        assert output.verifiable_claims == 1
        assert len(output.claims) == 1

