"""
Prompts module for The Undertow.

Contains production-grade prompts and few-shot examples.
"""

from undertow.prompts.few_shot_examples import (
    FEW_SHOT_EXAMPLES,
    get_few_shot_examples,
    FewShotExample,
)

__all__ = [
    "FEW_SHOT_EXAMPLES",
    "get_few_shot_examples",
    "FewShotExample",
]
