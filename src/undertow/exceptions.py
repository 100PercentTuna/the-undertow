"""
Exception hierarchy for The Undertow.

ALL exceptions MUST inherit from UndertowError.
NO bare Exception raises allowed.
"""

from typing import Any


class UndertowError(Exception):
    """Base exception for all Undertow errors."""

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} (details: {self.details})"
        return self.message


# =============================================================================
# Domain Errors
# =============================================================================


class DomainError(UndertowError):
    """Errors in domain/business logic."""

    pass


class ValidationError(DomainError):
    """Input or output validation failed."""

    pass


class BusinessRuleViolation(DomainError):
    """Business rule was violated."""

    pass


class EntityNotFoundError(DomainError):
    """Requested entity does not exist."""

    def __init__(self, entity_type: str, entity_id: str) -> None:
        super().__init__(
            f"{entity_type} with id '{entity_id}' not found",
            details={"entity_type": entity_type, "entity_id": entity_id},
        )


class DuplicateEntityError(DomainError):
    """Entity already exists."""

    def __init__(self, entity_type: str, identifier: str) -> None:
        super().__init__(
            f"{entity_type} already exists: {identifier}",
            details={"entity_type": entity_type, "identifier": identifier},
        )


# =============================================================================
# Infrastructure Errors
# =============================================================================


class InfrastructureError(UndertowError):
    """Errors in infrastructure layer."""

    pass


class DatabaseError(InfrastructureError):
    """Database operation failed."""

    pass


class CacheError(InfrastructureError):
    """Cache operation failed."""

    pass


class ExternalServiceError(InfrastructureError):
    """External service call failed."""

    pass


# =============================================================================
# LLM Errors
# =============================================================================


class LLMError(ExternalServiceError):
    """LLM API call failed."""

    pass


class RateLimitError(LLMError):
    """Rate limit exceeded."""

    def __init__(
        self,
        provider: str,
        retry_after: float | None = None,
    ) -> None:
        super().__init__(
            f"Rate limit exceeded for {provider}",
            details={"provider": provider, "retry_after": retry_after},
        )
        self.provider = provider
        self.retry_after = retry_after


class ContextLengthError(LLMError):
    """Input exceeds model context length."""

    def __init__(self, max_tokens: int, actual_tokens: int) -> None:
        super().__init__(
            f"Context length exceeded: {actual_tokens} > {max_tokens}",
            details={"max_tokens": max_tokens, "actual_tokens": actual_tokens},
        )
        self.max_tokens = max_tokens
        self.actual_tokens = actual_tokens


class ProviderUnavailableError(LLMError):
    """LLM provider is temporarily unavailable."""

    pass


class InvalidResponseError(LLMError):
    """LLM returned an invalid response."""

    pass


# =============================================================================
# Agent Errors
# =============================================================================


class AgentError(UndertowError):
    """Errors in agent execution."""

    pass


class AgentConfigurationError(AgentError):
    """Agent is misconfigured."""

    pass


class AgentExecutionError(AgentError):
    """Agent execution failed."""

    def __init__(
        self,
        agent_name: str,
        message: str,
        *,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(
            f"Agent '{agent_name}' failed: {message}",
            details={"agent_name": agent_name, "cause": str(cause) if cause else None},
        )
        self.agent_name = agent_name
        self.__cause__ = cause


class OutputParseError(AgentError):
    """Could not parse agent output."""

    def __init__(
        self,
        agent_name: str,
        error: str,
        raw_output: str | None = None,
    ) -> None:
        super().__init__(
            f"Failed to parse output from agent '{agent_name}': {error}",
            details={
                "agent_name": agent_name,
                "error": error,
                "raw_output_preview": raw_output[:500] if raw_output else None,
            },
        )


class OutputValidationError(AgentError):
    """Agent output failed schema validation."""

    def __init__(
        self,
        agent_name: str,
        errors: list[dict[str, Any]],
        raw_output: str | None = None,
    ) -> None:
        super().__init__(
            f"Output validation failed for agent '{agent_name}'",
            details={
                "agent_name": agent_name,
                "validation_errors": errors,
                "raw_output_preview": raw_output[:500] if raw_output else None,
            },
        )
        self.validation_errors = errors


# =============================================================================
# Pipeline Errors
# =============================================================================


class PipelineError(UndertowError):
    """Errors in pipeline execution."""

    pass


class QualityGateFailure(PipelineError):
    """Quality gate threshold not met."""

    def __init__(
        self,
        gate_name: str,
        score: float,
        threshold: float,
        issues: list[str] | None = None,
    ) -> None:
        super().__init__(
            f"Quality gate '{gate_name}' failed: {score:.2f} < {threshold:.2f}",
            details={
                "gate_name": gate_name,
                "score": score,
                "threshold": threshold,
                "issues": issues or [],
            },
        )
        self.gate_name = gate_name
        self.score = score
        self.threshold = threshold


class HumanEscalationRequired(PipelineError):
    """Issue requires human review."""

    def __init__(
        self,
        reason: str,
        severity: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            f"Human escalation required ({severity}): {reason}",
            details={"reason": reason, "severity": severity, "context": context or {}},
        )
        self.reason = reason
        self.severity = severity


# =============================================================================
# Budget Errors
# =============================================================================


class BudgetError(UndertowError):
    """Budget-related errors."""

    pass


class BudgetExceededError(BudgetError):
    """Daily budget has been exceeded."""

    def __init__(self, daily_limit: float, current_spend: float) -> None:
        super().__init__(
            f"Daily budget exceeded: ${current_spend:.2f} / ${daily_limit:.2f}",
            details={"daily_limit": daily_limit, "current_spend": current_spend},
        )

