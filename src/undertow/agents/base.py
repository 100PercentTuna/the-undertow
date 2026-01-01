"""
Base agent class for all AI agents.

ALL agents MUST inherit from BaseAgent and implement the abstract methods.
"""

import json
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, ClassVar, Generic, TypeVar
from uuid import uuid4

import structlog
from pydantic import BaseModel, ValidationError

from undertow.agents.result import AgentMetadata, AgentResult
from undertow.exceptions import (
    AgentConfigurationError,
    AgentExecutionError,
    OutputParseError,
    OutputValidationError,
)
from undertow.llm.router import ModelRouter
from undertow.llm.tiers import ModelTier

logger = structlog.get_logger()

InputT = TypeVar("InputT", bound=BaseModel)
OutputT = TypeVar("OutputT", bound=BaseModel)


class BaseAgent(ABC, Generic[InputT, OutputT]):
    """
    Abstract base class for all agents.

    EVERY agent MUST:
    1. Inherit from this class with proper type parameters
    2. Define task_name, version, input_schema, output_schema
    3. Implement _build_messages() and _parse_output()
    4. Return AgentResult (not raw output)
    """

    # REQUIRED: Class variables that MUST be defined by subclasses
    task_name: ClassVar[str]
    version: ClassVar[str]
    input_schema: ClassVar[type[BaseModel]]
    output_schema: ClassVar[type[BaseModel]]

    # OPTIONAL: Model tier for this agent (default: STANDARD)
    default_tier: ClassVar[ModelTier] = ModelTier.STANDARD

    def __init__(
        self,
        router: ModelRouter,
        *,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> None:
        """
        Initialize agent.

        Args:
            router: Model router for LLM calls
            temperature: Default temperature for generation
            max_tokens: Default max tokens for generation
        """
        self.router = router
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Validate configuration
        self._validate_configuration()

    def _validate_configuration(self) -> None:
        """Validate agent is properly configured."""
        required_attrs = ["task_name", "version", "input_schema", "output_schema"]
        for attr in required_attrs:
            if not hasattr(self.__class__, attr) or getattr(self.__class__, attr) is None:
                raise AgentConfigurationError(
                    f"Agent {self.__class__.__name__} missing required "
                    f"class variable: {attr}"
                )

    async def run(self, input_data: InputT) -> AgentResult[OutputT]:
        """
        Execute the agent.

        This is the ONLY public method for agent execution.
        Do not override this method - implement the abstract methods instead.

        Args:
            input_data: Validated input matching input_schema

        Returns:
            AgentResult containing output or error
        """
        execution_id = str(uuid4())
        started_at = datetime.utcnow()
        retries = 0

        logger.info(
            "Agent execution started",
            agent=self.task_name,
            execution_id=execution_id,
        )

        try:
            # Build messages
            messages = self._build_messages(input_data)

            # Call LLM
            response = await self.router.complete(
                task_name=self.task_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                force_tier=self.default_tier,
            )

            # Parse output
            output = self._parse_output(response.content)

            # Validate output schema
            validated_output = self._validate_output(output)

            # Assess quality
            quality_score = await self._assess_quality(validated_output, input_data)

            completed_at = datetime.utcnow()
            duration_ms = int((completed_at - started_at).total_seconds() * 1000)

            metadata = AgentMetadata(
                agent_name=self.task_name,
                agent_version=self.version,
                execution_id=execution_id,
                started_at=started_at,
                completed_at=completed_at,
                duration_ms=duration_ms,
                model_used=self.router.last_model_used,
                input_tokens=self.router.last_input_tokens,
                output_tokens=self.router.last_output_tokens,
                cost_usd=self.router.last_cost,
                quality_score=quality_score,
                retries=retries,
                cache_hit=False,
            )

            logger.info(
                "Agent execution completed",
                agent=self.task_name,
                execution_id=execution_id,
                duration_ms=duration_ms,
                quality_score=quality_score,
            )

            return AgentResult.ok(validated_output, metadata)

        except (OutputParseError, OutputValidationError) as e:
            completed_at = datetime.utcnow()
            duration_ms = int((completed_at - started_at).total_seconds() * 1000)

            logger.error(
                "Agent output error",
                agent=self.task_name,
                execution_id=execution_id,
                error=str(e),
            )

            metadata = AgentMetadata(
                agent_name=self.task_name,
                agent_version=self.version,
                execution_id=execution_id,
                started_at=started_at,
                completed_at=completed_at,
                duration_ms=duration_ms,
                model_used=self.router.last_model_used,
                input_tokens=self.router.last_input_tokens,
                output_tokens=self.router.last_output_tokens,
                cost_usd=self.router.last_cost,
                quality_score=None,
                retries=retries,
                cache_hit=False,
            )

            return AgentResult.fail(str(e), metadata)

        except Exception as e:
            completed_at = datetime.utcnow()
            duration_ms = int((completed_at - started_at).total_seconds() * 1000)

            logger.error(
                "Agent execution failed",
                agent=self.task_name,
                execution_id=execution_id,
                error=str(e),
            )

            metadata = AgentMetadata(
                agent_name=self.task_name,
                agent_version=self.version,
                execution_id=execution_id,
                started_at=started_at,
                completed_at=completed_at,
                duration_ms=duration_ms,
                model_used=getattr(self.router, "last_model_used", ""),
                input_tokens=getattr(self.router, "last_input_tokens", 0),
                output_tokens=getattr(self.router, "last_output_tokens", 0),
                cost_usd=getattr(self.router, "last_cost", 0.0),
                quality_score=None,
                retries=retries,
                cache_hit=False,
            )

            return AgentResult.fail(str(e), metadata)

    @abstractmethod
    def _build_messages(self, input_data: InputT) -> list[dict[str, str]]:
        """
        Build LLM messages from input.

        MUST be implemented by all agents.

        Args:
            input_data: Validated input

        Returns:
            List of message dicts with 'role' and 'content'
        """
        pass

    @abstractmethod
    def _parse_output(self, content: str) -> OutputT:
        """
        Parse LLM response into output schema.

        MUST be implemented by all agents.

        Args:
            content: Raw LLM response content

        Returns:
            Parsed output matching output_schema

        Raises:
            OutputParseError: If parsing fails
        """
        pass

    async def _assess_quality(
        self,
        output: OutputT,
        input_data: InputT,
    ) -> float:
        """
        Assess output quality.

        Override in subclasses for custom quality assessment.
        Default implementation returns 1.0 (assume good quality).

        Args:
            output: Parsed and validated output
            input_data: Original input

        Returns:
            Quality score from 0.0 to 1.0
        """
        return 1.0

    def _validate_output(self, output: Any) -> OutputT:
        """
        Validate output against schema.

        Args:
            output: Output to validate

        Returns:
            Validated output

        Raises:
            OutputValidationError: If validation fails
        """
        if isinstance(output, self.output_schema):
            return output  # type: ignore

        try:
            if isinstance(output, dict):
                return self.output_schema.model_validate(output)  # type: ignore
            else:
                return self.output_schema.model_validate(output.model_dump())  # type: ignore
        except ValidationError as e:
            raise OutputValidationError(
                agent_name=self.task_name,
                errors=e.errors(),
            ) from e

    def _extract_json(self, content: str) -> dict[str, Any]:
        """
        Extract JSON from LLM response.

        Handles cases where JSON is wrapped in markdown code blocks.

        Args:
            content: Raw response content

        Returns:
            Parsed JSON dict

        Raises:
            OutputParseError: If JSON extraction fails
        """
        # Try direct JSON parse first
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # Try to extract from markdown code block
        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            if end > start:
                try:
                    return json.loads(content[start:end].strip())
                except json.JSONDecodeError:
                    pass

        # Try to find JSON object
        if "{" in content:
            start = content.find("{")
            end = content.rfind("}") + 1
            if end > start:
                try:
                    return json.loads(content[start:end])
                except json.JSONDecodeError:
                    pass

        raise OutputParseError(
            agent_name=self.task_name,
            error="Could not extract valid JSON from response",
            raw_output=content,
        )

