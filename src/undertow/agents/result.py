"""
Agent result types.

Standardized result containers for all agent executions.
"""

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T", bound=BaseModel)


class AgentMetadata(BaseModel):
    """Metadata from agent execution."""

    agent_name: str = Field(..., description="Name of the agent")
    agent_version: str = Field(..., description="Version of the agent")
    execution_id: str = Field(..., description="Unique execution identifier")
    started_at: datetime = Field(..., description="Execution start time")
    completed_at: datetime = Field(..., description="Execution completion time")
    duration_ms: int = Field(..., ge=0, description="Duration in milliseconds")
    model_used: str = Field(..., description="LLM model used")
    input_tokens: int = Field(..., ge=0, description="Input tokens consumed")
    output_tokens: int = Field(..., ge=0, description="Output tokens generated")
    cost_usd: float = Field(..., ge=0, description="Cost in USD")
    quality_score: float | None = Field(None, ge=0, le=1, description="Quality score")
    retries: int = Field(0, ge=0, description="Number of retries")
    cache_hit: bool = Field(False, description="Whether result was from cache")


class AgentResult(BaseModel, Generic[T]):
    """
    Standardized result wrapper for all agents.

    Every agent MUST return this type, not raw output.
    """

    success: bool = Field(..., description="Whether execution succeeded")
    output: T | None = Field(None, description="Agent output if successful")
    error: str | None = Field(None, description="Error message if failed")
    metadata: AgentMetadata = Field(..., description="Execution metadata")

    @property
    def is_success(self) -> bool:
        """Check if execution was successful."""
        return self.success and self.output is not None

    @property
    def is_failure(self) -> bool:
        """Check if execution failed."""
        return not self.success

    @classmethod
    def ok(
        cls,
        output: T,
        metadata: AgentMetadata,
    ) -> "AgentResult[T]":
        """Create successful result."""
        return cls(success=True, output=output, error=None, metadata=metadata)

    @classmethod
    def fail(
        cls,
        error: str,
        metadata: AgentMetadata,
    ) -> "AgentResult[T]":
        """Create failed result."""
        return cls(success=False, output=None, error=error, metadata=metadata)

