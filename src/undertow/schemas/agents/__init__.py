"""
Agent-specific schemas for input/output contracts.
"""

from undertow.schemas.agents.motivation import (
    MotivationInput,
    MotivationOutput,
    MotivationLayer1,
    MotivationLayer2,
    MotivationLayer3,
    MotivationLayer4,
    MotivationSynthesis,
    StoryContext,
    AnalysisContext,
    ActorProfile,
)
from undertow.schemas.agents.chains import (
    ChainsInput,
    ChainsOutput,
    RippleMap,
    CuiBonoAnalysis,
    ChainsSynthesis,
)

__all__ = [
    # Motivation
    "MotivationInput",
    "MotivationOutput",
    "MotivationLayer1",
    "MotivationLayer2",
    "MotivationLayer3",
    "MotivationLayer4",
    "MotivationSynthesis",
    # Chains
    "ChainsInput",
    "ChainsOutput",
    "RippleMap",
    "CuiBonoAnalysis",
    "ChainsSynthesis",
    # Shared
    "StoryContext",
    "AnalysisContext",
    "ActorProfile",
]

