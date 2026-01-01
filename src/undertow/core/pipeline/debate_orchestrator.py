"""
Debate Orchestrator for adversarial review.

Coordinates the 3-agent debate protocol:
1. Challenger raises challenges
2. Advocate responds
3. Judge rules
"""

from dataclasses import dataclass, field
from typing import Any

import structlog

from undertow.agents.adversarial.debate import (
    ChallengerAgent,
    AdvocateAgent,
    JudgeAgent,
)
from undertow.llm.router import ModelRouter
from undertow.schemas.agents.debate import (
    ChallengerInput,
    ChallengerOutput,
    AdvocateInput,
    AdvocateOutput,
    JudgeInput,
    JudgeOutput,
    DebateChallenge,
    AdvocateResponse,
    JudgeRuling,
    DebateRound,
    DebateSummary,
)

logger = structlog.get_logger()


@dataclass
class DebateResult:
    """Result of a complete debate."""

    success: bool
    rounds: list[DebateRound] = field(default_factory=list)
    summary: DebateSummary | None = None
    total_cost: float = 0.0
    error: str | None = None


class DebateOrchestrator:
    """
    Orchestrates the adversarial debate protocol.

    The debate consists of multiple rounds where:
    1. Challenger identifies weaknesses in the analysis
    2. Advocate defends or acknowledges each challenge
    3. Judge rules on each challenge-response pair

    Example:
        orchestrator = DebateOrchestrator(router)
        result = await orchestrator.run_debate(
            analysis_summary="...",
            key_claims=["claim1", "claim2"],
            max_rounds=3,
        )
    """

    def __init__(
        self,
        router: ModelRouter,
        max_rounds: int = 3,
        min_challenges_per_round: int = 2,
    ) -> None:
        """
        Initialize debate orchestrator.

        Args:
            router: Model router for LLM calls
            max_rounds: Maximum debate rounds
            min_challenges_per_round: Minimum challenges to generate per round
        """
        self.router = router
        self.max_rounds = max_rounds
        self.min_challenges_per_round = min_challenges_per_round

        # Initialize agents
        self.challenger = ChallengerAgent(router, temperature=0.8)
        self.advocate = AdvocateAgent(router, temperature=0.7)
        self.judge = JudgeAgent(router, temperature=0.5)

    async def run_debate(
        self,
        analysis_summary: str,
        key_claims: list[str],
        motivation_synthesis: str = "",
        chains_synthesis: str = "",
        original_analysis: str = "",
    ) -> DebateResult:
        """
        Run the full debate protocol.

        Args:
            analysis_summary: Summary of the analysis to debate
            key_claims: Key claims to challenge
            motivation_synthesis: Motivation analysis synthesis
            chains_synthesis: Chains analysis synthesis
            original_analysis: Full analysis text for advocate

        Returns:
            DebateResult with all rounds and summary
        """
        logger.info("Starting debate protocol", max_rounds=self.max_rounds)

        rounds: list[DebateRound] = []
        all_challenges: list[DebateChallenge] = []
        total_cost = 0.0

        try:
            for round_num in range(1, self.max_rounds + 1):
                logger.info(f"Debate round {round_num}")

                # Step 1: Generate challenges
                challenger_input = ChallengerInput(
                    analysis_summary=analysis_summary,
                    key_claims=key_claims,
                    motivation_synthesis=motivation_synthesis,
                    chains_synthesis=chains_synthesis,
                    prior_challenges=all_challenges,
                )

                challenger_result = await self.challenger.run(challenger_input)

                if not challenger_result.success or not challenger_result.output:
                    logger.warning("Challenger failed", error=challenger_result.error)
                    break

                total_cost += challenger_result.metadata.cost_usd
                challenges = challenger_result.output.challenges

                if not challenges:
                    logger.info("No more challenges raised, debate complete")
                    break

                # Process each challenge
                for challenge in challenges:
                    # Step 2: Advocate responds
                    advocate_input = AdvocateInput(
                        original_analysis=original_analysis or analysis_summary,
                        challenge=challenge,
                        available_evidence=[],  # Could be enriched
                    )

                    advocate_result = await self.advocate.run(advocate_input)

                    if not advocate_result.success or not advocate_result.output:
                        logger.warning(
                            "Advocate failed",
                            challenge_id=challenge.challenge_id,
                        )
                        continue

                    total_cost += advocate_result.metadata.cost_usd
                    response = advocate_result.output.response

                    # Step 3: Judge rules
                    judge_input = JudgeInput(
                        original_claim=challenge.target_claim,
                        challenge=challenge,
                        response=response,
                        context=f"Round {round_num} of adversarial debate",
                    )

                    judge_result = await self.judge.run(judge_input)

                    if not judge_result.success or not judge_result.output:
                        logger.warning(
                            "Judge failed",
                            challenge_id=challenge.challenge_id,
                        )
                        continue

                    total_cost += judge_result.metadata.cost_usd
                    ruling = judge_result.output.ruling

                    # Record the round
                    debate_round = DebateRound(
                        round_number=round_num,
                        challenge=challenge,
                        response=response,
                        ruling=ruling,
                    )
                    rounds.append(debate_round)
                    all_challenges.append(challenge)

                    logger.info(
                        "Challenge processed",
                        challenge_id=challenge.challenge_id,
                        ruling=ruling.ruling,
                    )

            # Generate summary
            summary = self._generate_summary(rounds)

            logger.info(
                "Debate complete",
                total_rounds=len(rounds),
                sustained=summary.challenges_sustained,
                overruled=summary.challenges_overruled,
                total_cost=total_cost,
            )

            return DebateResult(
                success=True,
                rounds=rounds,
                summary=summary,
                total_cost=total_cost,
            )

        except Exception as e:
            logger.error("Debate failed", error=str(e))
            return DebateResult(
                success=False,
                rounds=rounds,
                total_cost=total_cost,
                error=str(e),
            )

    def _generate_summary(self, rounds: list[DebateRound]) -> DebateSummary:
        """Generate summary from debate rounds."""
        sustained = sum(1 for r in rounds if r.ruling.ruling == "challenge_sustained")
        overruled = sum(1 for r in rounds if r.ruling.ruling == "challenge_overruled")
        partial = sum(1 for r in rounds if r.ruling.ruling == "partial_sustain")

        # Collect required modifications
        modifications = [
            r.ruling.action_details
            for r in rounds
            if r.ruling.required_action not in ["no_change"]
            and r.ruling.action_details
        ]

        # Collect insights
        insights = []
        for r in rounds:
            if r.ruling.ruling == "challenge_sustained":
                insights.append(f"Valid challenge on: {r.challenge.target_claim[:50]}...")
            elif r.ruling.ruling == "partial_sustain":
                insights.append(f"Partial issue with: {r.challenge.target_claim[:50]}...")

        # Calculate confidence adjustment
        # Sustained challenges lower confidence, overruled raises it slightly
        adjustment = -0.05 * sustained + 0.02 * overruled - 0.02 * partial
        adjustment = max(-0.3, min(0.1, adjustment))  # Clamp

        return DebateSummary(
            total_rounds=len(rounds),
            challenges_sustained=sustained,
            challenges_overruled=overruled,
            challenges_partial=partial,
            required_modifications=modifications,
            analysis_strengthened=overruled > sustained,
            final_confidence_adjustment=adjustment,
            key_insights_from_debate=insights[:5],  # Top 5
        )

    async def quick_challenge(
        self,
        claim: str,
        context: str = "",
    ) -> dict[str, Any]:
        """
        Quick single-claim challenge for testing.

        Args:
            claim: Claim to challenge
            context: Additional context

        Returns:
            Challenge result
        """
        challenger_input = ChallengerInput(
            analysis_summary=context or claim,
            key_claims=[claim],
            prior_challenges=[],
        )

        result = await self.challenger.run(challenger_input)

        if result.success and result.output:
            return {
                "success": True,
                "challenges": [c.model_dump() for c in result.output.challenges],
                "assessment": result.output.overall_assessment,
            }
        else:
            return {
                "success": False,
                "error": result.error,
            }

