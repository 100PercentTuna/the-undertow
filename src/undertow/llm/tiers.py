"""
Model tier definitions and configurations.

Defines the model hierarchy and task-to-tier routing.
"""

from dataclasses import dataclass
from enum import Enum


class ModelTier(str, Enum):
    """Model tiers from highest to lowest capability."""

    FRONTIER = "frontier"  # Best quality, highest cost
    HIGH = "high"  # Strong quality, moderate cost
    STANDARD = "standard"  # Good quality, lower cost
    FAST = "fast"  # Quick responses, lowest cost


@dataclass(frozen=True)
class ModelConfig:
    """Configuration for a specific model."""

    provider: str
    model_id: str
    input_cost_per_1m: float  # Cost per 1M input tokens
    output_cost_per_1m: float  # Cost per 1M output tokens
    context_window: int
    supports_vision: bool = False
    supports_function_calling: bool = True


# Model configurations by provider and tier
ANTHROPIC_MODELS: dict[ModelTier, ModelConfig] = {
    ModelTier.FRONTIER: ModelConfig(
        provider="anthropic",
        model_id="claude-sonnet-4-20250514",
        input_cost_per_1m=3.0,
        output_cost_per_1m=15.0,
        context_window=200000,
        supports_vision=True,
    ),
    ModelTier.HIGH: ModelConfig(
        provider="anthropic",
        model_id="claude-sonnet-4-20250514",
        input_cost_per_1m=3.0,
        output_cost_per_1m=15.0,
        context_window=200000,
        supports_vision=True,
    ),
    ModelTier.STANDARD: ModelConfig(
        provider="anthropic",
        model_id="claude-sonnet-4-20250514",
        input_cost_per_1m=3.0,
        output_cost_per_1m=15.0,
        context_window=200000,
    ),
    ModelTier.FAST: ModelConfig(
        provider="anthropic",
        model_id="claude-3-5-haiku-20241022",
        input_cost_per_1m=0.8,
        output_cost_per_1m=4.0,
        context_window=200000,
    ),
}

OPENAI_MODELS: dict[ModelTier, ModelConfig] = {
    ModelTier.FRONTIER: ModelConfig(
        provider="openai",
        model_id="gpt-4o",
        input_cost_per_1m=2.5,
        output_cost_per_1m=10.0,
        context_window=128000,
        supports_vision=True,
    ),
    ModelTier.HIGH: ModelConfig(
        provider="openai",
        model_id="gpt-4o",
        input_cost_per_1m=2.5,
        output_cost_per_1m=10.0,
        context_window=128000,
        supports_vision=True,
    ),
    ModelTier.STANDARD: ModelConfig(
        provider="openai",
        model_id="gpt-4o-mini",
        input_cost_per_1m=0.15,
        output_cost_per_1m=0.6,
        context_window=128000,
    ),
    ModelTier.FAST: ModelConfig(
        provider="openai",
        model_id="gpt-4o-mini",
        input_cost_per_1m=0.15,
        output_cost_per_1m=0.6,
        context_window=128000,
    ),
}

# All models by provider
MODELS: dict[str, dict[ModelTier, ModelConfig]] = {
    "anthropic": ANTHROPIC_MODELS,
    "openai": OPENAI_MODELS,
}


def get_model_config(provider: str, tier: ModelTier) -> ModelConfig:
    """Get model configuration for provider and tier."""
    if provider not in MODELS:
        raise ValueError(f"Unknown provider: {provider}")
    if tier not in MODELS[provider]:
        raise ValueError(f"Unknown tier {tier} for provider {provider}")
    return MODELS[provider][tier]


# Task-to-tier routing configuration
TASK_ROUTING: dict[str, ModelTier] = {
    # Collection Phase (FAST/STANDARD)
    "zone_scout": ModelTier.FAST,
    "story_scorer": ModelTier.STANDARD,
    "source_aggregator": ModelTier.FAST,
    "relevance_filter": ModelTier.FAST,
    # Pass 1: Foundation (STANDARD)
    "factual_reconstruction": ModelTier.STANDARD,
    "context_analysis": ModelTier.STANDARD,
    "actor_profiling": ModelTier.STANDARD,
    # Pass 2: Core Analysis (FRONTIER)
    "motivation_analysis": ModelTier.FRONTIER,
    "chain_mapping": ModelTier.FRONTIER,
    "subtlety_analysis": ModelTier.HIGH,
    "self_critique": ModelTier.HIGH,
    # Pass 3: Supplementary (HIGH)
    "theory_analysis": ModelTier.HIGH,
    "historical_parallel": ModelTier.HIGH,
    "geography_analysis": ModelTier.STANDARD,
    "shockwave_analysis": ModelTier.STANDARD,
    "uncertainty_calibration": ModelTier.STANDARD,
    # Pass 3: Adversarial (FRONTIER)
    "debate_advocate": ModelTier.FRONTIER,
    "debate_challenger": ModelTier.FRONTIER,
    "debate_judge": ModelTier.FRONTIER,
    # Pass 3: Verification (HIGH)
    "fact_checker": ModelTier.HIGH,
    "source_verifier": ModelTier.HIGH,
    "logic_auditor": ModelTier.HIGH,
    "bias_detector": ModelTier.STANDARD,
    # Pass 4: Production (FRONTIER)
    "article_writer": ModelTier.FRONTIER,
    "voice_calibration": ModelTier.HIGH,
    "quality_evaluation": ModelTier.HIGH,
    "preamble_writer": ModelTier.HIGH,
}


def get_tier_for_task(task_name: str) -> ModelTier:
    """Get recommended tier for a task."""
    return TASK_ROUTING.get(task_name, ModelTier.STANDARD)


# Provider preferences for specific tasks
PROVIDER_PREFERENCES: dict[str, str] = {
    # Anthropic excels at nuanced analysis and long-form writing
    "motivation_analysis": "anthropic",
    "chain_mapping": "anthropic",
    "subtlety_analysis": "anthropic",
    "article_writer": "anthropic",
    "debate_advocate": "anthropic",
    "debate_challenger": "anthropic",
    "debate_judge": "anthropic",
    "self_critique": "anthropic",
    "preamble_writer": "anthropic",
    # OpenAI excels at structured extraction
    "factual_reconstruction": "openai",
    "zone_scout": "openai",
    "story_scorer": "openai",
}


def get_preferred_provider(task_name: str, default: str = "anthropic") -> str:
    """Get preferred provider for a task."""
    return PROVIDER_PREFERENCES.get(task_name, default)

