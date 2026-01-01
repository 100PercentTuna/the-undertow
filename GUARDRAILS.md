# The Undertow — Engineering Guardrails

## A+ Quality Standards for Reliability, Correctness, and Maintainability

---

# EXECUTIVE SUMMARY

This document defines **mandatory guardrails** that ensure The Undertow codebase maintains A+ quality across all engineering dimensions. These are not suggestions—they are enforced through automated checks, CI/CD gates, and mandatory review processes.

**Philosophy**: Prevent problems at the source. Every guardrail should be automatable where possible, and any violation should block deployment.

---

# TABLE OF CONTENTS

1. [Reliability Guardrails](#section-1-reliability-guardrails)
2. [Correctness Guardrails](#section-2-correctness-guardrails)
3. [Maintainability Guardrails](#section-3-maintainability-guardrails)
4. [Architecture Guardrails](#section-4-architecture-guardrails)
5. [Separation of Concerns](#section-5-separation-of-concerns)
6. [Best Practices & Compatibility](#section-6-best-practices--compatibility)
7. [Non-Fragility Guardrails](#section-7-non-fragility-guardrails)
8. [Drift Prevention](#section-8-drift-prevention)
9. [Performance & Latency](#section-9-performance--latency)
10. [Agent Output Quality](#section-10-agent-output-quality)
11. [Documentation & Comments](#section-11-documentation--comments)
12. [Enforcement Mechanisms](#section-12-enforcement-mechanisms)

---

# SECTION 1: RELIABILITY GUARDRAILS

## 1.1 Error Handling Standards

### MANDATORY: All External Calls Must Have Error Handling

```python
# ❌ FORBIDDEN: Unhandled external calls
response = await client.post(url, data=payload)
result = response.json()

# ✅ REQUIRED: Comprehensive error handling
async def call_external_service(url: str, payload: dict) -> Result[dict, ServiceError]:
    """
    External call with full error handling.
    
    Returns:
        Result containing response data or typed error
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return Ok(response.json())
            
    except httpx.TimeoutException:
        logger.warning(f"Timeout calling {url}")
        return Err(ServiceError.TIMEOUT)
        
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error {e.response.status_code} from {url}")
        if e.response.status_code == 429:
            return Err(ServiceError.RATE_LIMITED)
        elif e.response.status_code >= 500:
            return Err(ServiceError.SERVER_ERROR)
        return Err(ServiceError.CLIENT_ERROR)
        
    except httpx.RequestError as e:
        logger.error(f"Request error calling {url}: {e}")
        return Err(ServiceError.NETWORK_ERROR)
        
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON response from {url}")
        return Err(ServiceError.INVALID_RESPONSE)
```

### MANDATORY: Retry Configuration for All AI Calls

```python
# src/undertow/llm/retry.py

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

# Standard retry decorator for LLM calls
LLM_RETRY = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception_type((
        RateLimitError,
        ServiceUnavailableError,
        ConnectionError,
        TimeoutError
    )),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True
)

# Usage - ALL LLM calls must use this decorator
@LLM_RETRY
async def complete(self, messages: list[dict], **kwargs) -> LLMResponse:
    ...
```

### MANDATORY: Circuit Breaker Pattern

```python
# src/undertow/llm/circuit_breaker.py

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject calls
    HALF_OPEN = "half_open"  # Testing recovery

@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5       # Failures before opening
    recovery_timeout: int = 60       # Seconds before half-open
    success_threshold: int = 3       # Successes to close

class CircuitBreaker:
    """
    Circuit breaker for external service calls.
    
    REQUIRED for:
    - All LLM provider calls
    - All external API calls
    - Database connections
    """
    
    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: datetime | None = None
    
    async def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        
        if self.state == CircuitState.OPEN:
            if self._should_attempt_recovery():
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitOpenError(f"Circuit {self.name} is open")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitState.OPEN
            logger.error(f"Circuit {self.name} opened after {self.failure_count} failures")
            
            # Alert on circuit open
            metrics.circuit_breaker_opened.labels(circuit=self.name).inc()
    
    def _on_success(self):
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                logger.info(f"Circuit {self.name} closed after recovery")
```

## 1.2 Fault Tolerance Requirements

### MANDATORY: Graceful Degradation

```python
# Every critical path must have fallback behavior

class PipelineOrchestrator:
    """
    Pipeline must complete even if individual components fail.
    """
    
    async def run_pass2(self, story: Story, pass1: Pass1Output) -> Pass2Output:
        """
        Pass 2 with graceful degradation.
        
        If motivation analysis fails, continue with reduced quality.
        If chain analysis fails, use simplified chains.
        Never fail the entire pipeline for a single component.
        """
        
        motivation = await self._run_with_fallback(
            primary=lambda: self.motivation_agent.run(story, pass1),
            fallback=lambda: self._simplified_motivation(story, pass1),
            component="motivation_analysis"
        )
        
        chains = await self._run_with_fallback(
            primary=lambda: self.chain_agent.run(story, pass1, motivation),
            fallback=lambda: self._simplified_chains(story),
            component="chain_analysis"
        )
        
        return Pass2Output(
            motivation=motivation,
            chains=chains,
            degraded=motivation.is_fallback or chains.is_fallback
        )
    
    async def _run_with_fallback(
        self,
        primary: Callable,
        fallback: Callable,
        component: str
    ):
        """Run primary with fallback on failure."""
        try:
            result = await primary()
            result.is_fallback = False
            return result
        except Exception as e:
            logger.error(f"{component} failed, using fallback: {e}")
            metrics.component_fallback.labels(component=component).inc()
            
            result = await fallback()
            result.is_fallback = True
            result.degradation_reason = str(e)
            return result
```

### MANDATORY: Health Checks

```python
# src/undertow/api/routes/health.py

from fastapi import APIRouter, Response
from src.undertow.services.health import HealthChecker

router = APIRouter()

@router.get("/health")
async def health_check() -> dict:
    """
    Basic health check - always responds if server is running.
    """
    return {"status": "healthy"}

@router.get("/health/ready")
async def readiness_check(checker: HealthChecker = Depends()) -> Response:
    """
    Readiness check - verifies all dependencies are available.
    
    Returns 503 if any critical dependency is unavailable.
    """
    checks = await checker.check_all()
    
    if all(c.healthy for c in checks.values()):
        return Response(
            content=json.dumps({"status": "ready", "checks": checks}),
            media_type="application/json"
        )
    else:
        return Response(
            content=json.dumps({"status": "not_ready", "checks": checks}),
            status_code=503,
            media_type="application/json"
        )

@router.get("/health/live")
async def liveness_check() -> dict:
    """
    Liveness check - verifies the application is not deadlocked.
    """
    # Check event loop responsiveness
    start = time.monotonic()
    await asyncio.sleep(0)
    latency = time.monotonic() - start
    
    return {
        "status": "alive",
        "event_loop_latency_ms": latency * 1000
    }

class HealthChecker:
    """
    REQUIRED health checks for all dependencies.
    """
    
    async def check_all(self) -> dict[str, HealthStatus]:
        return {
            "database": await self._check_database(),
            "redis": await self._check_redis(),
            "anthropic": await self._check_anthropic(),
            "openai": await self._check_openai(),
        }
    
    async def _check_database(self) -> HealthStatus:
        try:
            async with self.db.acquire() as conn:
                await conn.execute("SELECT 1")
            return HealthStatus(healthy=True)
        except Exception as e:
            return HealthStatus(healthy=False, error=str(e))
```

## 1.3 Data Integrity Requirements

### MANDATORY: Database Transactions

```python
# All multi-step database operations MUST use transactions

# ❌ FORBIDDEN: Multiple writes without transaction
async def create_edition_bad(self, data: EditionCreate) -> Edition:
    edition = await self.edition_repo.create(data)
    for story_id in data.story_ids:
        await self.story_repo.update(story_id, {"edition_id": edition.id})
    return edition

# ✅ REQUIRED: Atomic transaction
async def create_edition(self, data: EditionCreate) -> Edition:
    """
    Create edition with all related updates atomically.
    
    If any step fails, entire operation is rolled back.
    """
    async with self.db.transaction():
        edition = await self.edition_repo.create(data)
        
        for story_id in data.story_ids:
            await self.story_repo.update(
                story_id, 
                {"edition_id": edition.id}
            )
        
        await self.audit_log.record(
            action="edition_created",
            resource_id=edition.id
        )
        
        return edition
```

### MANDATORY: Idempotency Keys

```python
# All mutating API endpoints MUST support idempotency

@router.post("/editions/{id}/publish")
async def publish_edition(
    id: UUID,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    service: EditionService = Depends()
) -> EditionResponse:
    """
    Publish edition with idempotency protection.
    
    Same idempotency key will return same result without re-executing.
    """
    # Check for existing result
    cached = await service.get_idempotent_result(idempotency_key)
    if cached:
        return cached
    
    # Execute operation
    result = await service.publish(id)
    
    # Cache result for idempotency
    await service.cache_idempotent_result(
        idempotency_key, 
        result,
        ttl_hours=24
    )
    
    return result
```

---

# SECTION 2: CORRECTNESS GUARDRAILS

## 2.1 Type Safety

### MANDATORY: Full Type Annotations

```python
# ❌ FORBIDDEN: Missing type annotations
def process_article(article, config):
    result = analyze(article)
    return result

# ✅ REQUIRED: Complete type annotations
from typing import TypeVar, Generic
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

async def process_article(
    article: Article,
    config: ProcessingConfig
) -> ProcessingResult:
    """
    Process article with full type safety.
    
    Args:
        article: Article to process
        config: Processing configuration
        
    Returns:
        ProcessingResult with analysis outputs
        
    Raises:
        ValidationError: If article data is invalid
        ProcessingError: If analysis fails
    """
    result: AnalysisOutput = await analyze(article, config)
    return ProcessingResult(
        article_id=article.id,
        analysis=result,
        processed_at=datetime.utcnow()
    )
```

### MANDATORY: Pydantic Models for All Data Structures

```python
# src/undertow/schemas/base.py

from pydantic import BaseModel, Field, validator
from datetime import datetime
from uuid import UUID

class StrictModel(BaseModel):
    """
    Base model with strict validation.
    
    ALL schemas must inherit from this.
    """
    
    class Config:
        # Forbid extra fields
        extra = "forbid"
        
        # Validate on assignment
        validate_assignment = True
        
        # Use enum values
        use_enum_values = True
        
        # Validate default values
        validate_default = True

# Example usage
class ArticleCreate(StrictModel):
    """
    Schema for creating articles.
    
    Strict validation ensures no invalid data enters system.
    """
    
    url: str = Field(..., min_length=10, max_length=2000)
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=100)
    source_id: UUID
    published_at: datetime
    
    @validator("url")
    def validate_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v
    
    @validator("published_at")
    def validate_not_future(cls, v: datetime) -> datetime:
        if v > datetime.utcnow():
            raise ValueError("Published date cannot be in the future")
        return v
```

## 2.2 Testing Requirements

### MANDATORY: Test Coverage Thresholds

```yaml
# pyproject.toml

[tool.coverage.run]
branch = true
source = ["src/undertow"]
omit = ["*/tests/*", "*/migrations/*"]

[tool.coverage.report]
# MANDATORY: Minimum coverage thresholds
fail_under = 80

# Per-module requirements
[tool.coverage.report.per_module]
"src/undertow/core/*" = 90      # Core logic: 90%
"src/undertow/agents/*" = 85    # Agents: 85%
"src/undertow/api/*" = 80       # API: 80%
"src/undertow/services/*" = 85  # Services: 85%
```

### MANDATORY: Test Categories

```python
# tests/conftest.py

import pytest

# Test markers for different categories
pytest.mark.unit        # Fast, isolated tests
pytest.mark.integration # Tests with real dependencies
pytest.mark.e2e         # End-to-end tests
pytest.mark.slow        # Tests > 5 seconds
pytest.mark.llm         # Tests that call LLM APIs

# MANDATORY: Every module must have tests in each category
"""
Required test structure:
tests/
├── unit/
│   ├── test_agents/
│   │   ├── test_motivation_agent.py     # Unit tests
│   │   └── test_chain_agent.py
│   └── test_services/
│       └── test_article_service.py
├── integration/
│   ├── test_pipeline_integration.py     # Integration tests
│   └── test_database_integration.py
└── e2e/
    └── test_full_pipeline.py            # E2E tests
"""

# MANDATORY fixtures
@pytest.fixture
def mock_llm_response():
    """All LLM-calling tests must use mocked responses by default."""
    with patch("src.undertow.llm.router.ModelRouter.complete") as mock:
        mock.return_value = LLMResponse(
            content='{"result": "test"}',
            input_tokens=100,
            output_tokens=50,
            model="test-model",
            latency_ms=100
        )
        yield mock
```

### MANDATORY: Property-Based Testing for Critical Logic

```python
# tests/unit/test_quality_gates.py

from hypothesis import given, strategies as st
from src.undertow.core.quality.gates import QualityGate

class TestQualityGateProperties:
    """
    Property-based tests ensure correctness across input space.
    """
    
    @given(
        score=st.floats(min_value=0.0, max_value=1.0),
        threshold=st.floats(min_value=0.0, max_value=1.0)
    )
    def test_gate_pass_iff_score_above_threshold(
        self, 
        score: float, 
        threshold: float
    ):
        """Gate passes if and only if score >= threshold."""
        gate = QualityGate(name="test", threshold=threshold)
        result = gate.evaluate_score(score)
        
        assert result.passed == (score >= threshold)
    
    @given(
        scores=st.lists(
            st.floats(min_value=0.0, max_value=1.0),
            min_size=1,
            max_size=10
        ),
        weights=st.lists(
            st.floats(min_value=0.0, max_value=1.0),
            min_size=1,
            max_size=10
        )
    )
    def test_weighted_score_in_valid_range(
        self, 
        scores: list[float], 
        weights: list[float]
    ):
        """Weighted score must always be in [0, 1]."""
        # Match lengths
        min_len = min(len(scores), len(weights))
        scores = scores[:min_len]
        weights = weights[:min_len]
        
        weighted = calculate_weighted_score(scores, weights)
        
        assert 0.0 <= weighted <= 1.0
```

## 2.3 Input Validation

### MANDATORY: Validate All External Input

```python
# src/undertow/api/deps.py

from fastapi import Depends, HTTPException, Query
from pydantic import BaseModel, validator
import re

class PaginationParams(BaseModel):
    """
    Validated pagination parameters.
    
    REQUIRED for all list endpoints.
    """
    
    page: int = Query(1, ge=1, le=10000)
    per_page: int = Query(50, ge=1, le=200)
    
class SearchParams(BaseModel):
    """
    Validated search parameters.
    
    Prevents injection and resource exhaustion.
    """
    
    query: str = Query(..., min_length=1, max_length=500)
    
    @validator("query")
    def sanitize_query(cls, v: str) -> str:
        # Remove potentially dangerous characters
        v = re.sub(r'[<>"\';]', '', v)
        # Limit consecutive spaces
        v = re.sub(r'\s+', ' ', v)
        return v.strip()

# MANDATORY: Use in all endpoints
@router.get("/articles")
async def list_articles(
    pagination: PaginationParams = Depends(),
    search: SearchParams | None = None
) -> ArticleListResponse:
    ...
```

### MANDATORY: LLM Output Validation

```python
# src/undertow/agents/validation.py

from pydantic import BaseModel, ValidationError
from typing import TypeVar, Type
import json

T = TypeVar("T", bound=BaseModel)

class OutputValidator:
    """
    MANDATORY validation for all LLM outputs.
    
    Every agent output must be validated before use.
    """
    
    @staticmethod
    def validate_json_output(
        content: str,
        schema: Type[T],
        agent_name: str
    ) -> T:
        """
        Validate and parse LLM JSON output.
        
        Raises:
            OutputValidationError: If output doesn't match schema
        """
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise OutputValidationError(
                agent=agent_name,
                error=f"Invalid JSON: {e}",
                raw_output=content
            )
        
        try:
            return schema.model_validate(data)
        except ValidationError as e:
            raise OutputValidationError(
                agent=agent_name,
                error=f"Schema validation failed: {e}",
                raw_output=content,
                validation_errors=e.errors()
            )
    
    @staticmethod
    def validate_confidence_bounds(
        value: float,
        field_name: str
    ) -> float:
        """All confidence values must be in [0, 1]."""
        if not 0.0 <= value <= 1.0:
            raise OutputValidationError(
                error=f"{field_name} must be between 0 and 1, got {value}"
            )
        return value
```

---

# SECTION 3: MAINTAINABILITY GUARDRAILS

## 3.1 Code Style Enforcement

### MANDATORY: Ruff Configuration

```toml
# pyproject.toml

[tool.ruff]
target-version = "py311"
line-length = 100
select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # pyflakes
    "I",      # isort
    "B",      # flake8-bugbear
    "C4",     # flake8-comprehensions
    "UP",     # pyupgrade
    "ARG",    # flake8-unused-arguments
    "SIM",    # flake8-simplify
    "TCH",    # flake8-type-checking
    "PTH",    # flake8-use-pathlib
    "ERA",    # eradicate (commented code)
    "PL",     # pylint
    "RUF",    # ruff-specific
]
ignore = [
    "PLR0913",  # Too many arguments (some agents need many)
]

[tool.ruff.per-file-ignores]
"tests/*" = ["ARG"]  # Allow unused arguments in tests

[tool.ruff.isort]
known-first-party = ["undertow"]
```

### MANDATORY: Pre-commit Hooks

```yaml
# .pre-commit-config.yaml

repos:
  # Formatting
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  # Type checking
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies:
          - pydantic>=2.0
          - types-redis

  # Security
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.7
    hooks:
      - id: bandit
        args: ["-c", "pyproject.toml"]

  # Secrets detection
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets

  # Commit message format
  - repo: https://github.com/commitizen-tools/commitizen
    rev: v3.13.0
    hooks:
      - id: commitizen
```

## 3.2 Naming Conventions

### MANDATORY: Consistent Naming

```python
# NAMING STANDARDS - ENFORCED BY CODE REVIEW

# Classes: PascalCase, descriptive nouns
class MotivationAnalysisAgent:     # ✅ Good
class motivation_agent:             # ❌ Bad: not PascalCase
class MAAgt:                        # ❌ Bad: unclear abbreviation

# Functions/Methods: snake_case, verb phrases
async def analyze_motivation():     # ✅ Good
async def motivation():             # ❌ Bad: not verb phrase
async def analyzeMotivation():      # ❌ Bad: not snake_case

# Variables: snake_case, descriptive
article_count = 10                  # ✅ Good
cnt = 10                           # ❌ Bad: unclear
articleCount = 10                  # ❌ Bad: not snake_case

# Constants: SCREAMING_SNAKE_CASE
MAX_RETRY_ATTEMPTS = 3             # ✅ Good
maxRetries = 3                     # ❌ Bad: not constant style

# Private members: single underscore prefix
def _internal_helper(self):        # ✅ Good
def __internal_helper(self):       # ❌ Bad: double underscore unless needed

# Type aliases: PascalCase
ArticleDict = dict[str, Any]       # ✅ Good
article_dict = dict[str, Any]      # ❌ Bad: not PascalCase
```

## 3.3 File Organization

### MANDATORY: Module Structure

```
# REQUIRED directory structure

src/undertow/
├── __init__.py                 # Package init, version
├── main.py                     # FastAPI app entry point
├── config.py                   # Pydantic Settings
│
├── api/                        # HTTP layer ONLY
│   ├── __init__.py
│   ├── routes/                 # Route definitions
│   │   ├── __init__.py
│   │   ├── articles.py
│   │   └── stories.py
│   ├── deps.py                 # Dependency injection
│   └── middleware.py           # Middleware
│
├── core/                       # Business logic
│   ├── __init__.py
│   ├── pipeline/               # Pipeline orchestration
│   └── quality/                # Quality systems
│
├── agents/                     # AI agents ONLY
│   ├── __init__.py
│   ├── base.py                 # Base agent class
│   ├── collection/
│   ├── analysis/
│   ├── adversarial/
│   └── production/
│
├── llm/                        # LLM infrastructure
│   ├── __init__.py
│   ├── providers/
│   ├── router.py
│   └── costs.py
│
├── models/                     # SQLAlchemy models ONLY
│   └── ...
│
├── schemas/                    # Pydantic schemas ONLY
│   └── ...
│
├── services/                   # Business services
│   └── ...
│
├── tasks/                      # Celery tasks
│   └── ...
│
└── utils/                      # Shared utilities
    └── ...

# RULES:
# 1. No business logic in api/ - only HTTP handling
# 2. No database access in agents/ - only analysis logic
# 3. All schemas in schemas/ - not scattered
# 4. All models in models/ - not scattered
```

---

# SECTION 4: ARCHITECTURE GUARDRAILS

## 4.1 Dependency Rules

### MANDATORY: Layered Architecture Enforcement

```python
# src/undertow/architecture.py

"""
DEPENDENCY RULES - ENFORCED BY IMPORT LINTER

Layer hierarchy (higher cannot import from lower):
1. api/          → Can import: core, services, schemas
2. tasks/        → Can import: core, services, schemas
3. services/     → Can import: core, models, schemas, llm
4. core/         → Can import: agents, schemas, llm
5. agents/       → Can import: schemas, llm
6. llm/          → Can import: schemas
7. models/       → Can import: (nothing internal)
8. schemas/      → Can import: (nothing internal)
9. utils/        → Can import: (nothing internal)

FORBIDDEN IMPORTS:
- models/ cannot import from services/
- agents/ cannot import from models/
- schemas/ cannot import from anything internal
- Circular imports of any kind
"""

# Enforcement via import-linter
# pyproject.toml:

# [tool.importlinter]
# root_package = "undertow"
# 
# [[tool.importlinter.contracts]]
# name = "Layered architecture"
# type = "layers"
# layers = [
#     "undertow.api",
#     "undertow.tasks",
#     "undertow.services",
#     "undertow.core",
#     "undertow.agents",
#     "undertow.llm",
#     "undertow.models",
#     "undertow.schemas",
# ]
```

### MANDATORY: Dependency Injection

```python
# src/undertow/api/deps.py

"""
ALL dependencies must be injected, never instantiated directly in handlers.
"""

from functools import lru_cache
from fastapi import Depends
from src.undertow.services.article_service import ArticleService
from src.undertow.llm.router import ModelRouter

# ❌ FORBIDDEN: Direct instantiation in route
@router.get("/articles")
async def list_articles_bad():
    service = ArticleService()  # Bad!
    return await service.list()

# ✅ REQUIRED: Dependency injection
@lru_cache
def get_model_router() -> ModelRouter:
    """Singleton model router."""
    return ModelRouter(
        providers=get_providers(),
        preference=settings.ai_provider_preference
    )

def get_article_service(
    db: AsyncSession = Depends(get_db),
    router: ModelRouter = Depends(get_model_router)
) -> ArticleService:
    """Factory for article service."""
    return ArticleService(db=db, router=router)

@router.get("/articles")
async def list_articles(
    service: ArticleService = Depends(get_article_service)
):
    return await service.list()
```

## 4.2 Interface Boundaries

### MANDATORY: Service Interfaces

```python
# src/undertow/services/interfaces.py

from abc import ABC, abstractmethod
from typing import Protocol

class ArticleServiceProtocol(Protocol):
    """
    Interface for article service.
    
    All implementations must follow this contract.
    Enables testing with mocks and future implementations.
    """
    
    async def get(self, id: UUID) -> Article | None:
        """Get article by ID."""
        ...
    
    async def list(
        self, 
        filters: ArticleFilters,
        pagination: Pagination
    ) -> PaginatedResult[Article]:
        """List articles with filters."""
        ...
    
    async def create(self, data: ArticleCreate) -> Article:
        """Create new article."""
        ...

# MANDATORY: Services must implement interfaces
class ArticleService(ArticleServiceProtocol):
    """
    Production article service implementation.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get(self, id: UUID) -> Article | None:
        ...
```

### MANDATORY: Agent Interfaces

```python
# src/undertow/agents/base.py

from abc import ABC, abstractmethod
from typing import TypeVar, Generic
from pydantic import BaseModel

InputT = TypeVar("InputT", bound=BaseModel)
OutputT = TypeVar("OutputT", bound=BaseModel)

class BaseAgent(ABC, Generic[InputT, OutputT]):
    """
    Abstract base for all agents.
    
    ALL agents MUST inherit from this and implement the interface.
    """
    
    # REQUIRED: Every agent must declare its task name
    task_name: str
    
    # REQUIRED: Every agent must declare input/output types
    input_schema: type[InputT]
    output_schema: type[OutputT]
    
    def __init__(self, router: ModelRouter):
        self.router = router
        self._validate_configuration()
    
    @abstractmethod
    async def run(self, input: InputT) -> OutputT:
        """
        Execute the agent.
        
        MUST be implemented by all agents.
        """
        pass
    
    @abstractmethod
    def _build_messages(self, input: InputT) -> list[dict]:
        """
        Build LLM messages from input.
        
        MUST be implemented by all agents.
        """
        pass
    
    def _validate_configuration(self):
        """Validate agent is properly configured."""
        if not self.task_name:
            raise AgentConfigurationError("task_name is required")
        if not self.input_schema:
            raise AgentConfigurationError("input_schema is required")
        if not self.output_schema:
            raise AgentConfigurationError("output_schema is required")
```

---

# SECTION 5: SEPARATION OF CONCERNS

## 5.1 Layer Responsibilities

### MANDATORY: Layer Boundaries

```python
# API LAYER - HTTP concerns ONLY
# src/undertow/api/routes/articles.py

@router.post("/articles", status_code=201)
async def create_article(
    data: ArticleCreateRequest,    # HTTP request parsing
    service: ArticleService = Depends()
) -> ArticleResponse:              # HTTP response formatting
    """
    API layer responsibilities:
    ✅ Parse HTTP request
    ✅ Validate request schema
    ✅ Call service
    ✅ Format HTTP response
    ✅ Handle HTTP errors
    
    ❌ NO business logic
    ❌ NO database access
    ❌ NO LLM calls
    """
    try:
        article = await service.create(data.to_domain())
        return ArticleResponse.from_domain(article)
    except DuplicateError:
        raise HTTPException(409, "Article already exists")

# SERVICE LAYER - Business logic
# src/undertow/services/article_service.py

class ArticleService:
    """
    Service layer responsibilities:
    ✅ Business logic
    ✅ Coordinate repositories
    ✅ Enforce business rules
    ✅ Transaction management
    
    ❌ NO HTTP concerns
    ❌ NO direct LLM calls (use agents)
    """
    
    async def create(self, data: ArticleCreate) -> Article:
        # Business validation
        if await self.repo.exists_by_url(data.url):
            raise DuplicateError(f"Article exists: {data.url}")
        
        # Business logic
        async with self.db.transaction():
            article = await self.repo.create(data)
            await self.process_article(article)
            return article

# AGENT LAYER - AI analysis ONLY
# src/undertow/agents/analysis/motivation.py

class MotivationAnalysisAgent(BaseAgent):
    """
    Agent layer responsibilities:
    ✅ Build prompts
    ✅ Call LLM via router
    ✅ Parse LLM output
    ✅ Validate output schema
    
    ❌ NO HTTP concerns
    ❌ NO database access
    ❌ NO business rules
    """
    
    async def run(self, input: MotivationInput) -> MotivationOutput:
        messages = self._build_messages(input)
        response = await self.router.complete(self.task_name, messages)
        return self._parse_output(response.content)
```

## 5.2 Cross-Cutting Concerns

### MANDATORY: Centralized Cross-Cutting Logic

```python
# LOGGING - Centralized configuration
# src/undertow/utils/logging.py

import structlog

def configure_logging():
    """
    Centralized logging configuration.
    
    ALL logging must go through structlog.
    """
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )

# Usage - consistent across all modules
logger = structlog.get_logger()
logger.info("article_created", article_id=str(article.id), source=source.name)

# METRICS - Centralized definitions
# src/undertow/utils/metrics.py

from prometheus_client import Counter, Histogram, Gauge

# ALL metrics defined in one place
class Metrics:
    # Pipeline metrics
    pipeline_duration = Histogram(
        "undertow_pipeline_duration_seconds",
        "Pipeline execution time",
        ["edition_id"]
    )
    
    # Agent metrics
    agent_calls = Counter(
        "undertow_agent_calls_total",
        "Agent invocation count",
        ["agent_name", "status"]
    )
    
    # Cost metrics
    llm_cost = Counter(
        "undertow_llm_cost_usd",
        "LLM API cost",
        ["provider", "model", "task"]
    )

metrics = Metrics()
```

---

# SECTION 6: BEST PRACTICES & COMPATIBILITY

## 6.1 Python Best Practices

### MANDATORY: Async Patterns

```python
# ✅ REQUIRED: Proper async patterns

# Concurrent execution when possible
async def process_stories(stories: list[Story]) -> list[Result]:
    """Process multiple stories concurrently."""
    return await asyncio.gather(
        *(process_story(s) for s in stories),
        return_exceptions=True
    )

# Semaphore for rate limiting
async def fetch_with_limit(urls: list[str], max_concurrent: int = 10):
    """Fetch URLs with concurrency limit."""
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def fetch_one(url: str):
        async with semaphore:
            return await fetch(url)
    
    return await asyncio.gather(*(fetch_one(u) for u in urls))

# Context managers for resources
async def process_with_db():
    """Always use context managers for resources."""
    async with get_db_session() as session:
        async with session.begin():
            # Work with session
            pass
    # Session automatically closed and committed/rolled back

# ❌ FORBIDDEN: Blocking calls in async context
async def bad_example():
    time.sleep(1)  # Blocks event loop!
    requests.get(url)  # Blocking HTTP!
    
# ✅ REQUIRED: Async equivalents
async def good_example():
    await asyncio.sleep(1)
    async with httpx.AsyncClient() as client:
        await client.get(url)
```

### MANDATORY: Context Managers

```python
# ALL resources must use context managers

# Database sessions
async with db.session() as session:
    ...

# HTTP clients
async with httpx.AsyncClient() as client:
    ...

# File operations
async with aiofiles.open(path) as f:
    ...

# Locks
async with lock:
    ...

# Custom resources must implement __aenter__/__aexit__
class ResourceManager:
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
        return False  # Don't suppress exceptions
```

## 6.2 Compatibility Standards

### MANDATORY: Version Pinning

```toml
# pyproject.toml

[project]
requires-python = ">=3.11,<3.13"

dependencies = [
    # Pin major.minor, allow patch updates
    "fastapi>=0.109.0,<0.110.0",
    "pydantic>=2.5.0,<3.0.0",
    "sqlalchemy>=2.0.0,<3.0.0",
    "celery>=5.3.0,<6.0.0",
    
    # AI SDKs - pin more strictly due to API changes
    "anthropic>=0.18.0,<0.19.0",
    "openai>=1.10.0,<2.0.0",
]

# Lock file MUST be committed
# poetry.lock or pdm.lock
```

### MANDATORY: Deprecation Handling

```python
# src/undertow/utils/deprecation.py

import warnings
from functools import wraps

def deprecated(
    reason: str,
    removal_version: str,
    replacement: str | None = None
):
    """
    Mark function as deprecated.
    
    REQUIRED: All deprecations must specify removal version.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            message = f"{func.__name__} is deprecated: {reason}"
            if replacement:
                message += f" Use {replacement} instead."
            message += f" Will be removed in {removal_version}."
            
            warnings.warn(message, DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Usage
@deprecated(
    reason="Old API style",
    removal_version="2.0.0",
    replacement="new_method()"
)
def old_method():
    ...
```

---

# SECTION 7: NON-FRAGILITY GUARDRAILS

## 7.1 Defensive Programming

### MANDATORY: Null Safety

```python
# ❌ FORBIDDEN: Assuming values exist
def process_bad(article: Article):
    title = article.metadata["title"]  # May raise KeyError
    author = article.author.name       # May raise AttributeError

# ✅ REQUIRED: Defensive access
def process_good(article: Article):
    # Dict access with default
    title = article.metadata.get("title", "Untitled")
    
    # Optional chaining equivalent
    author = article.author.name if article.author else "Unknown"
    
    # Or use proper Optional typing
    def get_author_name(article: Article) -> str:
        if article.author is None:
            return "Unknown"
        return article.author.name
```

### MANDATORY: Boundary Validation

```python
# src/undertow/utils/validation.py

def validate_bounds(
    value: float,
    min_val: float,
    max_val: float,
    name: str
) -> float:
    """
    Validate value is within bounds.
    
    REQUIRED for all external inputs and LLM outputs.
    """
    if not min_val <= value <= max_val:
        raise ValidationError(
            f"{name} must be between {min_val} and {max_val}, got {value}"
        )
    return value

def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value to bounds (when failing is not appropriate)."""
    return max(min_val, min(max_val, value))

# Usage in agents
class MotivationAgent:
    def _parse_output(self, content: str) -> MotivationOutput:
        data = json.loads(content)
        
        # Validate all confidence values
        for layer in ["layer1", "layer2", "layer3", "layer4"]:
            for field, assessment in data[layer].items():
                assessment["confidence"] = validate_bounds(
                    assessment["confidence"],
                    min_val=0.0,
                    max_val=1.0,
                    name=f"{layer}.{field}.confidence"
                )
        
        return MotivationOutput.model_validate(data)
```

## 7.2 Failure Isolation

### MANDATORY: Blast Radius Limitation

```python
# src/undertow/core/pipeline/isolation.py

class IsolatedExecution:
    """
    Execute components in isolation to prevent cascade failures.
    """
    
    @staticmethod
    async def run_isolated(
        func: Callable,
        timeout: float = 300.0,
        fallback: Any = None
    ) -> tuple[Any, bool]:
        """
        Run function with timeout and isolation.
        
        Returns:
            Tuple of (result, success)
        """
        try:
            result = await asyncio.wait_for(func(), timeout=timeout)
            return (result, True)
        except asyncio.TimeoutError:
            logger.error(f"Timeout in {func.__name__}")
            return (fallback, False)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            return (fallback, False)

# Usage in pipeline
async def run_pass3_supplementary(self, context: dict):
    """
    Supplementary analyses run in isolation.
    
    If one fails, others continue.
    """
    results = {}
    
    tasks = [
        ("theory", self.theory_agent.run),
        ("history", self.history_agent.run),
        ("geography", self.geography_agent.run),
    ]
    
    for name, func in tasks:
        result, success = await IsolatedExecution.run_isolated(
            lambda: func(context),
            timeout=60.0,
            fallback=None
        )
        results[name] = result
        
        if not success:
            metrics.agent_failure.labels(agent=name).inc()
    
    return results
```

---

# SECTION 8: DRIFT PREVENTION

## 8.1 Schema Drift

### MANDATORY: Database Migration Rules

```python
# migrations/rules.py

"""
DATABASE MIGRATION RULES

1. NEVER modify existing migrations
2. ALWAYS add new migration for schema changes
3. ALWAYS include rollback (downgrade)
4. NEVER delete columns in production (deprecate first)
5. ALWAYS add columns as nullable initially
6. Test migrations in staging before production
"""

# Example migration
# migrations/versions/2024_01_15_add_quality_score.py

from alembic import op
import sqlalchemy as sa

revision = "abc123"
down_revision = "xyz789"

def upgrade():
    # Add as nullable first
    op.add_column(
        "stories",
        sa.Column("quality_score", sa.Float, nullable=True)
    )
    
    # Backfill data
    op.execute(
        "UPDATE stories SET quality_score = 0.0 WHERE quality_score IS NULL"
    )
    
    # Then make non-nullable
    op.alter_column(
        "stories",
        "quality_score",
        nullable=False
    )

def downgrade():
    # REQUIRED: Always implement downgrade
    op.drop_column("stories", "quality_score")
```

### MANDATORY: API Versioning

```python
# src/undertow/api/versioning.py

from fastapi import APIRouter

# Version prefix for all routes
v1_router = APIRouter(prefix="/v1")
v2_router = APIRouter(prefix="/v2")

# RULES:
# 1. Never break existing endpoints
# 2. Deprecate before removing (6 month minimum)
# 3. New features can go in new version
# 4. Document all changes in changelog

# Deprecation header middleware
@app.middleware("http")
async def add_deprecation_headers(request: Request, call_next):
    response = await call_next(request)
    
    if request.url.path.startswith("/v1"):
        if request.url.path in DEPRECATED_ENDPOINTS:
            response.headers["Deprecation"] = "true"
            response.headers["Sunset"] = "2025-06-01"
            response.headers["Link"] = "</v2" + request.url.path + ">; rel=\"successor-version\""
    
    return response
```

## 8.2 Configuration Drift

### MANDATORY: Configuration Validation

```python
# src/undertow/config.py

from pydantic_settings import BaseSettings
from pydantic import validator, Field

class Settings(BaseSettings):
    """
    Application settings with validation.
    
    Configuration drift is prevented by:
    1. All config in one place
    2. Type validation
    3. Range validation
    4. Required fields enforced
    """
    
    # Database
    database_url: str = Field(..., description="PostgreSQL connection URL")
    database_pool_size: int = Field(20, ge=5, le=100)
    
    # AI
    anthropic_api_key: str = Field(..., description="Anthropic API key")
    openai_api_key: str | None = Field(None, description="OpenAI API key")
    ai_provider_preference: str = Field("anthropic")
    
    # Budget
    daily_budget_limit: float = Field(50.0, ge=1.0, le=1000.0)
    
    # Quality
    quality_gate_threshold: float = Field(0.80, ge=0.5, le=1.0)
    
    @validator("ai_provider_preference")
    def validate_provider(cls, v):
        if v not in ["anthropic", "openai", "best_fit"]:
            raise ValueError(f"Invalid provider: {v}")
        return v
    
    @validator("database_url")
    def validate_database_url(cls, v):
        if not v.startswith("postgresql"):
            raise ValueError("Only PostgreSQL is supported")
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# MANDATORY: Validate on startup
@app.on_event("startup")
async def validate_config():
    settings = Settings()  # Raises if invalid
    logger.info("Configuration validated", settings=settings.dict(exclude={"anthropic_api_key", "openai_api_key"}))
```

## 8.3 Prompt Drift

### MANDATORY: Prompt Version Control

```python
# prompts/versioning.py

"""
PROMPT VERSION CONTROL RULES

1. All prompts stored in prompts/ directory
2. Each prompt has version number
3. Changes require new version
4. Old versions kept for rollback
5. Performance tracked per version
"""

# prompts/analysis/motivation_v2.txt
"""
VERSION: 2.0.0
CREATED: 2024-01-15
AUTHOR: team
CHANGES: Added alternative hypothesis requirement

You are a senior intelligence analyst...
"""

# src/undertow/prompts/loader.py

class PromptLoader:
    """Load and version prompts."""
    
    def __init__(self, prompts_dir: str = "prompts"):
        self.prompts_dir = Path(prompts_dir)
        self._cache: dict[str, str] = {}
    
    def load(self, name: str, version: str = "latest") -> str:
        """
        Load prompt by name and version.
        
        Args:
            name: Prompt name (e.g., "analysis/motivation")
            version: Version or "latest"
        """
        cache_key = f"{name}:{version}"
        
        if cache_key not in self._cache:
            path = self._resolve_path(name, version)
            content = path.read_text()
            
            # Validate version header
            if "VERSION:" not in content:
                raise PromptError(f"Prompt {name} missing VERSION header")
            
            self._cache[cache_key] = content
        
        return self._cache[cache_key]
    
    def _resolve_path(self, name: str, version: str) -> Path:
        if version == "latest":
            # Find highest version
            pattern = f"{name}_v*.txt"
            versions = sorted(self.prompts_dir.glob(pattern))
            if not versions:
                raise PromptError(f"No prompts found for {name}")
            return versions[-1]
        else:
            return self.prompts_dir / f"{name}_v{version}.txt"
```

---

# SECTION 9: PERFORMANCE & LATENCY

## 9.1 Performance Requirements

### MANDATORY: Response Time SLOs

```python
# src/undertow/utils/slo.py

"""
SERVICE LEVEL OBJECTIVES

Endpoint Category    | P50    | P95    | P99
---------------------|--------|--------|--------
Health checks        | 10ms   | 50ms   | 100ms
List endpoints       | 100ms  | 500ms  | 1s
Detail endpoints     | 50ms   | 200ms  | 500ms
Create endpoints     | 200ms  | 1s     | 2s
Pipeline trigger     | 500ms  | 2s     | 5s

Background Tasks     | Max Duration
---------------------|-------------
Article ingestion    | 30s per article
Story analysis       | 5min per story
Full pipeline        | 90min total
"""

from functools import wraps
import time

def track_latency(endpoint_type: str):
    """Track endpoint latency against SLOs."""
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                return await func(*args, **kwargs)
            finally:
                latency = time.perf_counter() - start
                metrics.endpoint_latency.labels(
                    endpoint=func.__name__,
                    type=endpoint_type
                ).observe(latency)
                
                # Alert if exceeding SLO
                slo = SLO_THRESHOLDS[endpoint_type]
                if latency > slo["p95"]:
                    logger.warning(
                        "SLO breach",
                        endpoint=func.__name__,
                        latency=latency,
                        slo_p95=slo["p95"]
                    )
        return wrapper
    return decorator

# Usage
@router.get("/articles")
@track_latency("list")
async def list_articles(...):
    ...
```

### MANDATORY: Query Optimization

```python
# src/undertow/models/query_patterns.py

"""
QUERY OPTIMIZATION RULES

1. All list queries must have LIMIT
2. All queries must use indexes
3. N+1 queries are forbidden
4. Large result sets must use cursor pagination
"""

# ❌ FORBIDDEN: N+1 query
async def get_articles_bad(db: AsyncSession):
    articles = await db.execute(select(Article))
    for article in articles.scalars():
        # This triggers N additional queries!
        source = await db.execute(
            select(Source).where(Source.id == article.source_id)
        )

# ✅ REQUIRED: Eager loading
async def get_articles_good(db: AsyncSession):
    query = (
        select(Article)
        .options(selectinload(Article.source))  # Eager load
        .limit(100)  # Always limit
    )
    result = await db.execute(query)
    return result.scalars().all()

# ✅ REQUIRED: Cursor pagination for large datasets
async def list_articles_paginated(
    db: AsyncSession,
    cursor: str | None = None,
    limit: int = 50
) -> tuple[list[Article], str | None]:
    """
    Cursor-based pagination for consistent performance.
    """
    query = select(Article).order_by(Article.created_at.desc())
    
    if cursor:
        cursor_time = decode_cursor(cursor)
        query = query.where(Article.created_at < cursor_time)
    
    query = query.limit(limit + 1)  # Fetch one extra to check for more
    
    result = await db.execute(query)
    articles = result.scalars().all()
    
    if len(articles) > limit:
        next_cursor = encode_cursor(articles[limit - 1].created_at)
        return articles[:limit], next_cursor
    
    return articles, None
```

## 9.2 Caching Requirements

### MANDATORY: Cache Strategy

```python
# src/undertow/cache/strategy.py

"""
CACHING REQUIREMENTS

1. All expensive operations must be cached
2. Cache keys must include version
3. Cache invalidation must be explicit
4. TTLs must be documented
"""

from enum import Enum

class CacheTTL(Enum):
    """Standardized cache TTLs."""
    
    SHORT = 300           # 5 minutes - volatile data
    MEDIUM = 3600         # 1 hour - moderately stable
    LONG = 86400          # 1 day - stable data
    VERY_LONG = 604800    # 1 week - very stable

CACHE_CONFIG = {
    # LLM responses
    "llm_response": {
        "ttl": CacheTTL.MEDIUM,
        "key_template": "llm:{task}:{hash}:v1",
    },
    
    # Embeddings
    "embedding": {
        "ttl": CacheTTL.VERY_LONG,
        "key_template": "emb:{text_hash}:v1",
    },
    
    # Actor profiles
    "actor_profile": {
        "ttl": CacheTTL.LONG,
        "key_template": "actor:{id}:{date}:v1",
    },
    
    # Zone context
    "zone_context": {
        "ttl": CacheTTL.MEDIUM,
        "key_template": "zone:{zone_id}:{date}:v1",
    },
}

class CacheManager:
    """Centralized cache management."""
    
    async def get_or_compute(
        self,
        cache_type: str,
        key_params: dict,
        compute_fn: Callable,
    ):
        """Get from cache or compute and store."""
        
        config = CACHE_CONFIG[cache_type]
        key = config["key_template"].format(**key_params)
        
        # Try cache
        cached = await self.redis.get(key)
        if cached:
            metrics.cache_hit.labels(type=cache_type).inc()
            return json.loads(cached)
        
        # Compute
        metrics.cache_miss.labels(type=cache_type).inc()
        result = await compute_fn()
        
        # Store
        await self.redis.setex(
            key,
            config["ttl"].value,
            json.dumps(result)
        )
        
        return result
```

---

# SECTION 10: AGENT OUTPUT QUALITY

## 10.1 Output Validation

### MANDATORY: Schema Validation for All Agent Outputs

```python
# src/undertow/agents/validation.py

class AgentOutputValidator:
    """
    MANDATORY validation for all agent outputs.
    
    Every agent must validate its output before returning.
    """
    
    @staticmethod
    def validate_motivation_output(output: dict) -> MotivationOutput:
        """
        Validate motivation analysis output.
        
        Checks:
        1. All 4 layers present
        2. All confidence values in [0, 1]
        3. At least 2 alternative hypotheses
        4. Evidence cited for each assessment
        """
        errors = []
        
        # Check layers
        required_layers = ["layer1_individual", "layer2_institutional", 
                         "layer3_structural", "layer4_window"]
        for layer in required_layers:
            if layer not in output:
                errors.append(f"Missing required layer: {layer}")
        
        # Check confidences
        for layer_name, layer_data in output.items():
            if layer_name.startswith("layer"):
                for field, assessment in layer_data.items():
                    conf = assessment.get("confidence")
                    if conf is None:
                        errors.append(f"{layer_name}.{field}: missing confidence")
                    elif not 0 <= conf <= 1:
                        errors.append(f"{layer_name}.{field}: confidence {conf} not in [0,1]")
                    
                    if not assessment.get("evidence"):
                        errors.append(f"{layer_name}.{field}: missing evidence")
        
        # Check alternatives
        alternatives = output.get("synthesis", {}).get("alternative_hypotheses", [])
        if len(alternatives) < 2:
            errors.append(f"Need at least 2 alternatives, got {len(alternatives)}")
        
        if errors:
            raise OutputValidationError(
                agent="motivation_analysis",
                errors=errors,
                raw_output=output
            )
        
        return MotivationOutput.model_validate(output)
```

### MANDATORY: Quality Scoring for Outputs

```python
# src/undertow/agents/quality.py

class OutputQualityScorer:
    """
    Score agent output quality.
    
    Used for:
    1. Quality gate decisions
    2. Agent performance tracking
    3. Prompt optimization
    """
    
    async def score_motivation_output(
        self,
        output: MotivationOutput,
        context: AnalysisContext
    ) -> QualityScore:
        """
        Score motivation analysis quality.
        """
        scores = {}
        
        # Completeness: All sections filled
        scores["completeness"] = self._score_completeness(output)
        
        # Depth: Average content length and detail
        scores["depth"] = self._score_depth(output)
        
        # Confidence calibration: Reasonable confidence distribution
        scores["calibration"] = self._score_calibration(output)
        
        # Evidence grounding: Claims have evidence
        scores["grounding"] = self._score_grounding(output)
        
        # Alternatives quality: Genuine alternatives, not strawmen
        scores["alternatives"] = await self._score_alternatives(output, context)
        
        # Weighted average
        weights = {
            "completeness": 0.2,
            "depth": 0.25,
            "calibration": 0.15,
            "grounding": 0.25,
            "alternatives": 0.15,
        }
        
        overall = sum(scores[k] * weights[k] for k in scores)
        
        return QualityScore(
            overall=overall,
            dimensions=scores,
            passed=overall >= 0.80
        )
```

## 10.2 Output Consistency

### MANDATORY: Consistency Checks

```python
# src/undertow/agents/consistency.py

class ConsistencyChecker:
    """
    Check consistency across agent outputs.
    
    Catches contradictions between different analysis components.
    """
    
    async def check_cross_agent_consistency(
        self,
        pass1: Pass1Output,
        pass2: Pass2Output
    ) -> ConsistencyReport:
        """
        Check consistency between Pass 1 and Pass 2.
        """
        issues = []
        
        # Actors mentioned in motivation should exist in actor profiles
        motivation_actors = self._extract_actors(pass2.motivation)
        profiled_actors = {a.name for a in pass1.actors.individuals}
        
        missing = motivation_actors - profiled_actors
        if missing:
            issues.append(ConsistencyIssue(
                type="missing_actor_profile",
                severity="MEDIUM",
                message=f"Actors in motivation not profiled: {missing}"
            ))
        
        # Timeline in chains should be consistent with factual timeline
        chain_events = self._extract_timeline_events(pass2.chains)
        factual_events = {e.event for e in pass1.factual.timeline}
        
        for event in chain_events:
            if event.assumed_fact and event.assumed_fact not in factual_events:
                issues.append(ConsistencyIssue(
                    type="unverified_assumption",
                    severity="HIGH",
                    message=f"Chain assumes fact not in timeline: {event.assumed_fact}"
                ))
        
        return ConsistencyReport(
            consistent=len([i for i in issues if i.severity == "HIGH"]) == 0,
            issues=issues
        )
```

---

# SECTION 11: DOCUMENTATION & COMMENTS

## 11.1 Code Documentation Standards

### MANDATORY: Docstring Requirements

```python
# ALL public functions/classes MUST have docstrings

def analyze_motivation(
    story: Story,
    context: AnalysisContext,
    config: MotivationConfig | None = None
) -> MotivationOutput:
    """
    Analyze motivations behind the story's events.
    
    Performs four-layer motivation analysis:
    1. Individual decision-maker analysis
    2. Institutional interests mapping
    3. Structural pressures identification
    4. Opportunistic window assessment
    
    Args:
        story: Story to analyze with source articles
        context: Analysis context including actor profiles
        config: Optional configuration overrides
        
    Returns:
        MotivationOutput with all four layers and synthesis
        
    Raises:
        AnalysisError: If analysis fails after retries
        ValidationError: If output fails schema validation
        
    Example:
        >>> output = await analyze_motivation(story, context)
        >>> print(output.synthesis.primary_driver)
        "Layer 1: Individual political survival"
        
    Note:
        This function uses FRONTIER tier models and typically
        takes 30-60 seconds to complete.
    """
    ...

class MotivationAnalysisAgent(BaseAgent[MotivationInput, MotivationOutput]):
    """
    Agent for four-layer motivation analysis.
    
    Analyzes why actors took specific actions by examining:
    
    Layer 1 (Individual):
        Personal political position, domestic needs, psychology,
        relationships, and legacy considerations.
        
    Layer 2 (Institutional):
        Foreign ministry, military/intelligence, economic actors,
        and institutional momentum.
        
    Layer 3 (Structural):
        Systemic position, threat environment, economic structure,
        and geographic imperatives.
        
    Layer 4 (Opportunistic):
        What changed, position shifts, relaxed constraints,
        upcoming events, and factor convergence.
    
    Attributes:
        task_name: "motivation_analysis"
        input_schema: MotivationInput
        output_schema: MotivationOutput
        
    Example:
        >>> agent = MotivationAnalysisAgent(router)
        >>> output = await agent.run(input_data)
    """
```

### MANDATORY: Inline Comments for Complex Logic

```python
# Complex logic MUST have explanatory comments

async def calculate_verification_score(
    supporting: list[Assessment],
    contradicting: list[Assessment],
    independence: float
) -> float:
    """Calculate weighted verification score."""
    
    # Tier weights reflect source reliability hierarchy:
    # - Tier 1 (primary sources): Full weight
    # - Tier 2 (quality journalism): 80% weight
    # - Tier 3 (expert analysis): 50% weight
    # - Tier 4 (contextual): 20% weight
    TIER_WEIGHTS = {1: 1.0, 2: 0.8, 3: 0.5, 4: 0.2}
    
    # Calculate weighted support score
    # Higher tier sources contribute more to verification
    support_weight = sum(
        TIER_WEIGHTS.get(a.source.tier, 0.1)
        for a in supporting
    )
    
    # Contradiction from ANY tier reduces score
    # But higher tier contradictions are more damaging
    contradict_weight = sum(
        TIER_WEIGHTS.get(a.source.tier, 0.1)
        for a in contradicting
    )
    
    # Avoid division by zero when no sources found
    if support_weight + contradict_weight == 0:
        return 0.0
    
    # Base score is ratio of support to total evidence
    base_score = support_weight / (support_weight + contradict_weight)
    
    # Independence factor ensures we're not just seeing
    # the same original source cited multiple times.
    # Score is scaled: 50% base + 50% independence-adjusted
    # This prevents gaming by finding many citations of same source
    return base_score * (0.5 + 0.5 * independence)
```

## 11.2 API Documentation

### MANDATORY: OpenAPI Documentation

```python
# All API endpoints MUST have complete OpenAPI docs

@router.post(
    "/stories/{id}/analyze",
    response_model=AnalysisResponse,
    summary="Trigger story analysis",
    description="""
    Triggers the full analysis pipeline for a story.
    
    The pipeline runs asynchronously and includes:
    1. Pass 1: Foundation (factual reconstruction, context, actors)
    2. Pass 2: Core analysis (motivation, chains, subtleties)
    3. Pass 3: Verification (debate, fact-check, source verification)
    4. Pass 4: Production (article writing, voice calibration)
    
    Monitor progress via GET /stories/{id} or websocket subscription.
    """,
    responses={
        200: {
            "description": "Analysis triggered successfully",
            "content": {
                "application/json": {
                    "example": {
                        "story_id": "123e4567-e89b-12d3-a456-426614174000",
                        "status": "QUEUED",
                        "estimated_duration_minutes": 15
                    }
                }
            }
        },
        404: {"description": "Story not found"},
        409: {"description": "Analysis already in progress"},
        503: {"description": "Pipeline temporarily unavailable"}
    },
    tags=["stories"]
)
async def analyze_story(
    id: UUID = Path(..., description="Story ID to analyze"),
    priority: Priority = Query(Priority.NORMAL, description="Queue priority"),
    service: StoryService = Depends()
) -> AnalysisResponse:
    ...
```

---

# SECTION 12: ENFORCEMENT MECHANISMS

## 12.1 CI/CD Gates

### MANDATORY: Pipeline Stages

```yaml
# .github/workflows/ci.yml

name: CI Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  # Stage 1: Static Analysis
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      
      # Ruff linting - MUST PASS
      - name: Ruff lint
        run: ruff check src/ tests/
      
      # Ruff formatting - MUST PASS
      - name: Ruff format
        run: ruff format --check src/ tests/
      
      # Type checking - MUST PASS
      - name: MyPy
        run: mypy src/
      
      # Security scan - MUST PASS
      - name: Bandit
        run: bandit -r src/ -c pyproject.toml
      
      # Import structure - MUST PASS
      - name: Import linter
        run: lint-imports

  # Stage 2: Unit Tests
  test-unit:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      - name: Run unit tests
        run: pytest tests/unit -v --cov=src/undertow --cov-fail-under=80

  # Stage 3: Integration Tests
  test-integration:
    runs-on: ubuntu-latest
    needs: test-unit
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
      redis:
        image: redis:7
    steps:
      - uses: actions/checkout@v4
      - name: Run integration tests
        run: pytest tests/integration -v

  # Stage 4: E2E Tests (on main only)
  test-e2e:
    runs-on: ubuntu-latest
    needs: test-integration
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - name: Run E2E tests
        run: pytest tests/e2e -v

  # Stage 5: Build
  build:
    runs-on: ubuntu-latest
    needs: [test-unit, test-integration]
    steps:
      - uses: actions/checkout@v4
      - name: Build Docker image
        run: docker build -t undertow:${{ github.sha }} .
      
      - name: Push to registry
        run: |
          docker push undertow:${{ github.sha }}
```

## 12.2 Pre-commit Enforcement

```yaml
# .pre-commit-config.yaml - MANDATORY for all developers

default_install_hook_types: [pre-commit, commit-msg]

repos:
  # Code quality
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  # Type checking
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [pydantic>=2.0]

  # Security
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.7
    hooks:
      - id: bandit
        args: ["-c", "pyproject.toml"]

  # Secrets
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets

  # Commit messages
  - repo: https://github.com/commitizen-tools/commitizen
    rev: v3.13.0
    hooks:
      - id: commitizen
        stages: [commit-msg]

  # Documentation
  - repo: local
    hooks:
      - id: check-docstrings
        name: Check docstrings
        entry: python scripts/check_docstrings.py
        language: python
        types: [python]
```

## 12.3 Code Review Checklist

```markdown
# MANDATORY CODE REVIEW CHECKLIST

## Before Approving, Verify:

### Architecture
- [ ] Changes follow layered architecture
- [ ] No forbidden imports (check import-linter)
- [ ] New dependencies justified and approved

### Reliability
- [ ] All external calls have error handling
- [ ] Retries configured for transient failures
- [ ] Fallbacks exist for critical paths

### Correctness
- [ ] All functions have type annotations
- [ ] All inputs validated (Pydantic schemas)
- [ ] All outputs validated (for agents)
- [ ] Tests cover new code (80%+ coverage)

### Performance
- [ ] No N+1 queries
- [ ] Appropriate caching added
- [ ] Query limits in place

### Documentation
- [ ] Public functions have docstrings
- [ ] Complex logic has comments
- [ ] API endpoints have OpenAPI docs

### Security
- [ ] No secrets in code
- [ ] Input sanitization present
- [ ] SQL injection prevented (parameterized queries)

## Auto-Blocked If:
- CI pipeline fails
- Coverage below threshold
- Type errors present
- Security issues detected
```

## 12.4 Runtime Enforcement

```python
# src/undertow/runtime/guards.py

"""
Runtime guards that prevent violations during execution.
"""

import functools
from typing import Callable

def require_transaction(func: Callable):
    """
    Decorator ensuring function runs within transaction.
    
    Raises RuntimeError if called outside transaction.
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # Check if we're in a transaction
        session = kwargs.get('session') or args[0] if args else None
        if session and not session.in_transaction():
            raise RuntimeError(
                f"{func.__name__} must be called within a transaction"
            )
        return await func(*args, **kwargs)
    return wrapper

def require_authenticated(func: Callable):
    """Decorator ensuring request is authenticated."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        request = kwargs.get('request')
        if not request or not request.state.user:
            raise UnauthorizedError("Authentication required")
        return await func(*args, **kwargs)
    return wrapper

def enforce_budget(func: Callable):
    """Decorator checking budget before LLM calls."""
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        estimated_cost = self._estimate_cost(*args, **kwargs)
        if not await self.budget.can_spend(estimated_cost):
            raise BudgetExceededError(
                f"Insufficient budget for {func.__name__}"
            )
        return await func(self, *args, **kwargs)
    return wrapper
```

---

# APPENDIX A: GUARDRAIL SUMMARY

## Quick Reference Card

| Category | Key Guardrails | Enforcement |
|----------|---------------|-------------|
| **Reliability** | Error handling, retries, circuit breakers, health checks | CI + Runtime |
| **Correctness** | Type safety, Pydantic validation, 80%+ test coverage | CI |
| **Maintainability** | Ruff formatting, consistent naming, file organization | Pre-commit + CI |
| **Architecture** | Layered deps, dependency injection, interfaces | Import linter + Review |
| **Separation** | Layer boundaries, centralized cross-cutting | Review |
| **Best Practices** | Async patterns, context managers, version pinning | CI + Review |
| **Non-Fragility** | Null safety, boundary validation, failure isolation | CI + Runtime |
| **Drift Prevention** | Schema migrations, API versioning, prompt versions | CI + Review |
| **Performance** | SLOs, query optimization, caching | CI + Monitoring |
| **Agent Quality** | Output validation, quality scoring, consistency | Runtime |
| **Documentation** | Docstrings, inline comments, OpenAPI | Pre-commit + Review |

---

# APPENDIX B: VIOLATION SEVERITY

| Severity | Examples | Action |
|----------|----------|--------|
| **CRITICAL** | Security vulnerability, data loss risk | Block deploy, immediate fix |
| **HIGH** | Missing error handling, no tests | Block merge |
| **MEDIUM** | Missing docstring, suboptimal pattern | Fix before merge |
| **LOW** | Style inconsistency, minor naming | Fix when convenient |

---

*These guardrails are living documentation. Update as the system evolves.*

