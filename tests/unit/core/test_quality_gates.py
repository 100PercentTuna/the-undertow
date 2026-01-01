"""
Tests for quality gates.
"""

import pytest

from undertow.core.quality.gates import (
    FoundationGate,
    FoundationData,
    AnalysisGate,
    AnalysisData,
    AdversarialGate,
    AdversarialData,
    OutputGate,
    OutputData,
)
from undertow.exceptions import QualityGateFailure


class TestFoundationGate:
    """Tests for Foundation Gate."""

    def test_passes_with_good_data(self):
        """Test gate passes with good foundation data."""
        gate = FoundationGate()
        data = FoundationData(
            facts_verified=10,
            facts_total=10,
            sources_count=3,
            key_events_identified=5,
            actors_profiled=3,
            context_completeness=0.8,
        )
        
        result = gate.evaluate(data)
        
        assert result.passed
        assert result.score >= 0.75

    def test_fails_with_poor_data(self):
        """Test gate fails with poor foundation data."""
        gate = FoundationGate()
        data = FoundationData(
            facts_verified=2,
            facts_total=10,
            sources_count=1,
            key_events_identified=1,
            actors_profiled=1,
            context_completeness=0.3,
        )
        
        result = gate.evaluate(data)
        
        assert not result.passed
        assert result.score < 0.75
        assert len(result.issues) > 0

    def test_enforce_raises_on_failure(self):
        """Test enforce raises QualityGateFailure."""
        gate = FoundationGate()
        data = FoundationData(
            facts_verified=0,
            facts_total=10,
            sources_count=0,
            key_events_identified=0,
            actors_profiled=0,
            context_completeness=0.0,
        )
        
        with pytest.raises(QualityGateFailure) as exc_info:
            gate.enforce(data)
        
        assert exc_info.value.gate_name == "foundation"


class TestAnalysisGate:
    """Tests for Analysis Gate."""

    def test_passes_with_good_data(self):
        """Test gate passes with good analysis data."""
        gate = AnalysisGate()
        data = AnalysisData(
            motivation_analysis_score=0.85,
            chain_mapping_score=0.82,
            layer_completeness=0.9,
            alternative_hypotheses_count=3,
            confidence_calibration=0.8,
        )
        
        result = gate.evaluate(data)
        
        assert result.passed
        assert result.score >= 0.80

    def test_fails_without_alternatives(self):
        """Test gate flags insufficient alternative hypotheses."""
        gate = AnalysisGate()
        data = AnalysisData(
            motivation_analysis_score=0.85,
            chain_mapping_score=0.82,
            layer_completeness=0.9,
            alternative_hypotheses_count=1,  # Not enough
            confidence_calibration=0.8,
        )
        
        result = gate.evaluate(data)
        
        assert "Insufficient alternative hypotheses" in result.issues


class TestAdversarialGate:
    """Tests for Adversarial Gate."""

    def test_passes_with_good_data(self):
        """Test gate passes with good adversarial data."""
        gate = AdversarialGate()
        data = AdversarialData(
            fact_check_score=0.95,
            debate_resolution_score=0.85,
            bias_detection_score=0.9,
            logic_audit_score=0.88,
            unresolved_challenges=0,
        )
        
        result = gate.evaluate(data)
        
        assert result.passed
        assert result.score >= 0.80

    def test_penalizes_unresolved_challenges(self):
        """Test gate penalizes unresolved challenges."""
        gate = AdversarialGate()
        data = AdversarialData(
            fact_check_score=0.95,
            debate_resolution_score=0.85,
            bias_detection_score=0.9,
            logic_audit_score=0.88,
            unresolved_challenges=3,
        )
        
        result = gate.evaluate(data)
        
        assert "3 unresolved challenges" in result.issues


class TestOutputGate:
    """Tests for Output Gate."""

    def test_passes_with_good_data(self):
        """Test gate passes with good output data."""
        gate = OutputGate()
        data = OutputData(
            writing_quality_score=0.88,
            voice_consistency_score=0.9,
            source_citation_rate=0.95,
            uncertainty_acknowledgment=0.8,
            readability_score=0.85,
            length_appropriate=True,
        )
        
        result = gate.evaluate(data)
        
        assert result.passed
        assert result.score >= 0.85

    def test_penalizes_inappropriate_length(self):
        """Test gate penalizes inappropriate length."""
        gate = OutputGate()
        data = OutputData(
            writing_quality_score=0.9,
            voice_consistency_score=0.9,
            source_citation_rate=0.95,
            uncertainty_acknowledgment=0.9,
            readability_score=0.9,
            length_appropriate=False,
        )
        
        result = gate.evaluate(data)
        
        # Score should be reduced
        assert result.score < 0.9
        assert "Article length inappropriate" in result.issues

