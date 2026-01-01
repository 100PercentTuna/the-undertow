"""
Voice Calibration Agent.

Ensures article prose matches The Undertow's distinctive voice.
"""

from typing import ClassVar

import structlog

from undertow.agents.base import BaseAgent
from undertow.exceptions import OutputParseError
from undertow.llm.tiers import ModelTier
from undertow.schemas.agents.production import VoiceCalibrationInput, VoiceCalibrationOutput

logger = structlog.get_logger()


VOICE_SYSTEM_PROMPT = """You are the Voice Calibration editor for The Undertow, ensuring every piece matches our distinctive voice.

## THE UNDERTOW VOICE PROFILE

### Core Character
A brilliant friend who spent twenty years thinking about how power works—someone who explains the Iran nuclear deal over dinner without making you feel stupid, but who admits when something is genuinely confusing.

### Voice Dimensions

**Tone**: Serious but not solemn
- Stakes are real
- Self-importance is the enemy
- Wit welcome, flippancy forbidden

**Confidence**: Confident but not arrogant
- State positions clearly
- Acknowledge uncertainty
- Hold opinions lightly

**Density**: Dense but not impenetrable
- Every sentence works
- Complex ≠ convoluted
- Assume intelligence, not expertise

**Humanity**: Witty but never flip
- Well-placed observations sharpen attention
- Never at expense of suffering
- Dark humor only when earned

## FORBIDDEN PATTERNS

1. **Clichés** (MAJOR)
   - "In today's interconnected world..."
   - "Time will tell..."
   - "Remains to be seen..."
   - "Only time will tell..."
   - "At the end of the day..."

2. **Agency Erasure** (MAJOR)
   - "Violence erupted" → WHO committed violence
   - "Tensions escalated" → WHO escalated
   - "Conflict broke out" → WHO started fighting
   - Passive voice hiding actors

3. **Hedging Excess** (MODERATE)
   - "It could be argued that..."
   - "Some might say..."
   - "In some ways..."
   - "Perhaps one could consider..."

4. **Overconfidence** (MAJOR)
   - "Clearly..."
   - "Obviously..."
   - "Without doubt..."
   - Predictions without uncertainty

5. **Jargon** (MODERATE)
   - Unexplained acronyms
   - IR theory terms without context
   - Diplomatic-speak without translation

6. **Condescension** (MAJOR)
   - Explaining the obvious
   - "As everyone knows..."
   - Over-simplifying for readers

## ISSUE SEVERITY

- **minor**: Style preference, optional fix
- **moderate**: Should fix, affects voice
- **major**: Must fix, violates core principles

## YOUR TASK

Scan the article for voice issues.
For each issue, provide:
- Location in text
- Issue type
- Original problematic text
- Why it's an issue
- Suggested fix
- Severity

Then provide:
- Overall voice consistency score
- Tone assessment
- Strengths identified

Output as valid JSON matching VoiceCalibrationOutput schema."""


class VoiceCalibrationAgent(BaseAgent[VoiceCalibrationInput, VoiceCalibrationOutput]):
    """
    Voice Calibration agent - ensures voice consistency.
    
    Uses HIGH tier for nuanced style analysis.
    """

    task_name: ClassVar[str] = "voice_calibration"
    version: ClassVar[str] = "1.0.0"
    input_schema: ClassVar[type] = VoiceCalibrationInput
    output_schema: ClassVar[type] = VoiceCalibrationOutput
    default_tier: ClassVar[ModelTier] = ModelTier.HIGH

    def _build_messages(self, input_data: VoiceCalibrationInput) -> list[dict[str, str]]:
        """Build messages for voice calibration."""
        user_content = f"""## ARTICLE TO REVIEW

{input_data.article_content}

## TARGET VOICE PROFILE

{input_data.target_voice}

## YOUR TASK

1. Scan for voice issues (forbidden patterns, tone mismatches, etc.)
2. Assess overall voice consistency
3. Identify strengths
4. If significant issues, provide corrected version

Output as valid JSON matching VoiceCalibrationOutput schema."""

        return [
            {"role": "system", "content": VOICE_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

    def _parse_output(self, content: str) -> VoiceCalibrationOutput:
        """Parse voice calibration output."""
        try:
            data = self._extract_json(content)
            return VoiceCalibrationOutput.model_validate(data)
        except Exception as e:
            logger.error("Failed to parse voice calibration output", error=str(e))
            raise OutputParseError(
                agent_name=self.task_name,
                error=str(e),
                raw_output=content,
            ) from e

    async def _assess_quality(
        self,
        output: VoiceCalibrationOutput,
        input_data: VoiceCalibrationInput,
    ) -> float:
        """Assess quality of voice review."""
        # Quality is based on thoroughness of review
        scores: list[float] = []

        # Did we find issues proportional to content length?
        content_length = len(input_data.article_content)
        expected_issues_min = content_length // 2000  # ~1 issue per 2000 chars
        issue_coverage = min(1.0, len(output.issues) / max(1, expected_issues_min))
        scores.append(issue_coverage)

        # Did we provide assessment?
        assessment_quality = 1.0 if len(output.tone_assessment) >= 50 else 0.5
        scores.append(assessment_quality)

        # Did we identify strengths?
        strengths_quality = 1.0 if len(output.strengths) >= 2 else 0.7
        scores.append(strengths_quality)

        return sum(scores) / len(scores)

