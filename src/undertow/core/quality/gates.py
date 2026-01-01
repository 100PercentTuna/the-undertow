"""
Quality gate implementations.

The 4-gate quality system ensures consistent output quality:
1. Foundation Gate (75%) - After Pass 1
2. Analysis Gate (80%) - After Pass 2 
3. Adversarial Gate (80%) - After Pass 3
4. Output Gate (85%) - Before publication
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

import structlog

from undertow.config import settings
from undertow.exceptions import QualityGateFailure

logger = structlog.get_logger()

T = TypeVar("T")


@dataclass
class QualityGateResult:
    """Result of a quality gate evaluation."""

    gate_name: str
    passed: bool
    score: float
    threshold: float
    issues: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.passed = self.score >= self.threshold


class QualityGate(ABC, Generic[T]):
    """
    Abstract base class for quality gates.

    Each gate evaluates a specific aspect of the pipeline output
    and enforces a minimum quality threshold.
    """

    gate_name: str
    threshold: float

    @abstractmethod
    def evaluate(self, data: T) -> QualityGateResult:
        """
        Evaluate data against this gate's criteria.

        Args:
            data: Data to evaluate

        Returns:
            QualityGateResult with score and issues
        """
        pass

    def enforce(self, data: T) -> QualityGateResult:
        """
        Evaluate and raise if gate fails.

        Args:
            data: Data to evaluate

        Returns:
            QualityGateResult if passed

        Raises:
            QualityGateFailure: If score below threshold
        """
        result = self.evaluate(data)

        logger.info(
            "Quality gate evaluation",
            gate=self.gate_name,
            score=result.score,
            threshold=result.threshold,
            passed=result.passed,
            issues_count=len(result.issues),
        )

        if not result.passed:
            raise QualityGateFailure(
                gate_name=self.gate_name,
                score=result.score,
                threshold=result.threshold,
                issues=result.issues,
            )

        return result


@dataclass
class FoundationData:
    """Data for Foundation Gate evaluation."""

    facts_verified: int
    facts_total: int
    sources_count: int
    key_events_identified: int
    actors_profiled: int
    context_completeness: float


class FoundationGate(QualityGate[FoundationData]):
    """
    Gate 1: Foundation Quality.

    Evaluates:
    - Fact verification rate
    - Source diversity
    - Event identification
    - Actor profiling
    - Context completeness
    """

    gate_name = "foundation"
    threshold = settings.quality_gate_foundation

    def evaluate(self, data: FoundationData) -> QualityGateResult:
        """Evaluate foundation quality."""
        issues: list[str] = []
        scores: list[tuple[str, float, float]] = []

        # Fact verification rate (30%)
        if data.facts_total > 0:
            fact_rate = data.facts_verified / data.facts_total
        else:
            fact_rate = 0.0
            issues.append("No facts to verify")
        scores.append(("fact_verification", fact_rate, 0.30))

        # Source diversity (20%)
        source_score = min(1.0, data.sources_count / 3)  # 3+ sources = 100%
        if data.sources_count < 2:
            issues.append(f"Insufficient sources: {data.sources_count}")
        scores.append(("source_diversity", source_score, 0.20))

        # Event identification (15%)
        event_score = min(1.0, data.key_events_identified / 5)
        if data.key_events_identified < 2:
            issues.append("Too few key events identified")
        scores.append(("event_identification", event_score, 0.15))

        # Actor profiling (15%)
        actor_score = min(1.0, data.actors_profiled / 3)
        if data.actors_profiled < 2:
            issues.append("Insufficient actor profiling")
        scores.append(("actor_profiling", actor_score, 0.15))

        # Context completeness (20%)
        if data.context_completeness < 0.6:
            issues.append("Context incomplete")
        scores.append(("context_completeness", data.context_completeness, 0.20))

        # Calculate weighted score
        total_score = sum(score * weight for _, score, weight in scores)

        return QualityGateResult(
            gate_name=self.gate_name,
            passed=total_score >= self.threshold,
            score=total_score,
            threshold=self.threshold,
            issues=issues,
            details={name: score for name, score, _ in scores},
        )


@dataclass
class AnalysisData:
    """Data for Analysis Gate evaluation."""

    motivation_analysis_score: float
    chain_mapping_score: float
    layer_completeness: float  # All 4 motivation layers
    alternative_hypotheses_count: int
    confidence_calibration: float


class AnalysisGate(QualityGate[AnalysisData]):
    """
    Gate 2: Analysis Quality.

    Evaluates:
    - Motivation analysis depth
    - Chain mapping completeness
    - Layer coverage
    - Alternative hypotheses
    - Confidence calibration
    """

    gate_name = "analysis"
    threshold = settings.quality_gate_analysis

    def evaluate(self, data: AnalysisData) -> QualityGateResult:
        """Evaluate analysis quality."""
        issues: list[str] = []
        scores: list[tuple[str, float, float]] = []

        # Motivation analysis (30%)
        if data.motivation_analysis_score < 0.7:
            issues.append("Motivation analysis below standard")
        scores.append(("motivation_analysis", data.motivation_analysis_score, 0.30))

        # Chain mapping (25%)
        if data.chain_mapping_score < 0.7:
            issues.append("Chain mapping below standard")
        scores.append(("chain_mapping", data.chain_mapping_score, 0.25))

        # Layer completeness (20%)
        if data.layer_completeness < 0.8:
            issues.append("Not all motivation layers fully analyzed")
        scores.append(("layer_completeness", data.layer_completeness, 0.20))

        # Alternative hypotheses (15%)
        alt_score = min(1.0, data.alternative_hypotheses_count / 2)
        if data.alternative_hypotheses_count < 2:
            issues.append("Insufficient alternative hypotheses")
        scores.append(("alternative_hypotheses", alt_score, 0.15))

        # Confidence calibration (10%)
        if data.confidence_calibration < 0.6:
            issues.append("Poor confidence calibration")
        scores.append(("confidence_calibration", data.confidence_calibration, 0.10))

        total_score = sum(score * weight for _, score, weight in scores)

        return QualityGateResult(
            gate_name=self.gate_name,
            passed=total_score >= self.threshold,
            score=total_score,
            threshold=self.threshold,
            issues=issues,
            details={name: score for name, score, _ in scores},
        )


@dataclass
class AdversarialData:
    """Data for Adversarial Gate evaluation."""

    fact_check_score: float
    debate_resolution_score: float
    bias_detection_score: float
    logic_audit_score: float
    unresolved_challenges: int


class AdversarialGate(QualityGate[AdversarialData]):
    """
    Gate 3: Adversarial Review Quality.

    Evaluates:
    - Fact checking results
    - Debate resolution
    - Bias detection
    - Logic audit
    - Unresolved challenges
    """

    gate_name = "adversarial"
    threshold = settings.quality_gate_adversarial

    def evaluate(self, data: AdversarialData) -> QualityGateResult:
        """Evaluate adversarial review quality."""
        issues: list[str] = []
        scores: list[tuple[str, float, float]] = []

        # Fact check (30%)
        if data.fact_check_score < 0.9:
            issues.append("Fact check found issues")
        scores.append(("fact_check", data.fact_check_score, 0.30))

        # Debate resolution (25%)
        if data.debate_resolution_score < 0.7:
            issues.append("Unresolved debate challenges")
        scores.append(("debate_resolution", data.debate_resolution_score, 0.25))

        # Bias detection (20%)
        scores.append(("bias_detection", data.bias_detection_score, 0.20))

        # Logic audit (15%)
        if data.logic_audit_score < 0.8:
            issues.append("Logic audit found issues")
        scores.append(("logic_audit", data.logic_audit_score, 0.15))

        # Unresolved challenges penalty (10%)
        unresolved_score = max(0, 1.0 - (data.unresolved_challenges * 0.2))
        if data.unresolved_challenges > 0:
            issues.append(f"{data.unresolved_challenges} unresolved challenges")
        scores.append(("unresolved_challenges", unresolved_score, 0.10))

        total_score = sum(score * weight for _, score, weight in scores)

        return QualityGateResult(
            gate_name=self.gate_name,
            passed=total_score >= self.threshold,
            score=total_score,
            threshold=self.threshold,
            issues=issues,
            details={name: score for name, score, _ in scores},
        )


@dataclass
class OutputData:
    """Data for Output Gate evaluation."""

    writing_quality_score: float
    voice_consistency_score: float
    source_citation_rate: float
    uncertainty_acknowledgment: float
    readability_score: float
    length_appropriate: bool


class OutputGate(QualityGate[OutputData]):
    """
    Gate 4: Output Quality.

    Evaluates:
    - Writing quality
    - Voice consistency
    - Source citation
    - Uncertainty acknowledgment
    - Readability
    - Appropriate length
    """

    gate_name = "output"
    threshold = settings.quality_gate_output

    def evaluate(self, data: OutputData) -> QualityGateResult:
        """Evaluate output quality."""
        issues: list[str] = []
        scores: list[tuple[str, float, float]] = []

        # Writing quality (30%)
        if data.writing_quality_score < 0.8:
            issues.append("Writing quality below standard")
        scores.append(("writing_quality", data.writing_quality_score, 0.30))

        # Voice consistency (25%)
        if data.voice_consistency_score < 0.8:
            issues.append("Voice inconsistency detected")
        scores.append(("voice_consistency", data.voice_consistency_score, 0.25))

        # Source citation (20%)
        if data.source_citation_rate < 0.9:
            issues.append("Insufficient source citations")
        scores.append(("source_citation", data.source_citation_rate, 0.20))

        # Uncertainty acknowledgment (15%)
        if data.uncertainty_acknowledgment < 0.7:
            issues.append("Insufficient uncertainty acknowledgment")
        scores.append(("uncertainty_acknowledgment", data.uncertainty_acknowledgment, 0.15))

        # Readability (10%)
        scores.append(("readability", data.readability_score, 0.10))

        # Length penalty
        if not data.length_appropriate:
            issues.append("Article length inappropriate")

        total_score = sum(score * weight for _, score, weight in scores)

        # Apply length penalty
        if not data.length_appropriate:
            total_score *= 0.9

        return QualityGateResult(
            gate_name=self.gate_name,
            passed=total_score >= self.threshold,
            score=total_score,
            threshold=self.threshold,
            issues=issues,
            details={name: score for name, score, _ in scores},
        )

