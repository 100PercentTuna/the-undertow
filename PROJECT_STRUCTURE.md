# The Undertow — Project Structure

## Best-Practice Python Project Organization

---

# COMPLETE PROJECT STRUCTURE

```
the-undertow/
│
├── 📄 README.md                          # Project overview
├── 📄 LICENSE                            # License file
├── 📄 pyproject.toml                     # Project configuration (Poetry)
├── 📄 poetry.lock                        # Locked dependencies
├── 📄 .python-version                    # Python version (3.11)
│
├── 📄 Makefile                           # Common commands
├── 📄 Dockerfile                         # Production container
├── 📄 Dockerfile.dev                     # Development container
├── 📄 docker-compose.yml                 # Local development stack
├── 📄 docker-compose.prod.yml            # Production stack
│
├── 📄 .env.example                       # Environment template
├── 📄 .gitignore                         # Git ignores
├── 📄 .dockerignore                      # Docker ignores
├── 📄 .pre-commit-config.yaml            # Pre-commit hooks
│
├── 📁 .github/                           # GitHub configuration
│   ├── 📁 workflows/
│   │   ├── 📄 ci.yml                     # CI pipeline
│   │   ├── 📄 cd.yml                     # CD pipeline
│   │   ├── 📄 security.yml               # Security scanning
│   │   └── 📄 release.yml                # Release automation
│   ├── 📁 ISSUE_TEMPLATE/
│   │   ├── 📄 bug_report.yml
│   │   └── 📄 feature_request.yml
│   ├── 📄 PULL_REQUEST_TEMPLATE.md
│   ├── 📄 CODEOWNERS
│   └── 📄 dependabot.yml
│
├── 📁 docs/                              # Documentation (generated)
│   ├── 📄 index.md
│   ├── 📁 architecture/
│   ├── 📁 api/
│   └── 📁 agents/
│
├── 📁 scripts/                           # Utility scripts
│   ├── 📄 setup_dev.sh                   # Dev environment setup
│   ├── 📄 run_migrations.py              # Database migrations
│   ├── 📄 seed_data.py                   # Seed test data
│   ├── 📄 check_docstrings.py            # Docstring validation
│   └── 📄 generate_openapi.py            # OpenAPI spec generation
│
├── 📁 prompts/                           # LLM prompt templates (versioned)
│   ├── 📁 collection/
│   │   ├── 📄 zone_scout_v1.txt
│   │   └── 📄 story_scorer_v1.txt
│   ├── 📁 analysis/
│   │   ├── 📄 motivation_v1.txt
│   │   ├── 📄 motivation_v2.txt          # Version history preserved
│   │   ├── 📄 chain_mapping_v1.txt
│   │   └── 📄 subtlety_v1.txt
│   ├── 📁 adversarial/
│   │   ├── 📄 advocate_v1.txt
│   │   ├── 📄 challenger_v1.txt
│   │   └── 📄 judge_v1.txt
│   └── 📁 production/
│       ├── 📄 article_writer_v1.txt
│       ├── 📄 voice_calibration_v1.txt
│       └── 📄 preamble_writer_v1.txt
│
├── 📁 migrations/                        # Alembic migrations
│   ├── 📄 env.py
│   ├── 📄 alembic.ini
│   └── 📁 versions/
│       ├── 📄 0001_initial_schema.py
│       └── 📄 0002_add_quality_tables.py
│
├── 📁 tests/                             # Test suite
│   ├── 📄 __init__.py
│   ├── 📄 conftest.py                    # Shared fixtures
│   ├── 📄 factories.py                   # Test data factories
│   │
│   ├── 📁 unit/                          # Unit tests (fast, isolated)
│   │   ├── 📄 __init__.py
│   │   ├── 📁 agents/
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 test_base_agent.py
│   │   │   ├── 📄 test_motivation_agent.py
│   │   │   ├── 📄 test_chain_agent.py
│   │   │   └── 📄 test_debate_agents.py
│   │   ├── 📁 core/
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 test_pipeline.py
│   │   │   └── 📄 test_quality_gates.py
│   │   ├── 📁 services/
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 test_article_service.py
│   │   │   └── 📄 test_story_service.py
│   │   └── 📁 llm/
│   │       ├── 📄 __init__.py
│   │       ├── 📄 test_router.py
│   │       └── 📄 test_providers.py
│   │
│   ├── 📁 integration/                   # Integration tests
│   │   ├── 📄 __init__.py
│   │   ├── 📄 test_database.py
│   │   ├── 📄 test_pipeline_integration.py
│   │   └── 📄 test_api_integration.py
│   │
│   ├── 📁 e2e/                           # End-to-end tests
│   │   ├── 📄 __init__.py
│   │   └── 📄 test_full_pipeline.py
│   │
│   └── 📁 golden/                        # Golden tests (expected outputs)
│       ├── 📁 motivation/
│       │   ├── 📄 somaliland_input.json
│       │   └── 📄 somaliland_expected.json
│       └── 📁 chains/
│           ├── 📄 ukraine_input.json
│           └── 📄 ukraine_expected.json
│
└── 📁 src/                               # Source code
    └── 📁 undertow/                      # Main package
        ├── 📄 __init__.py                # Package init, version
        ├── 📄 main.py                    # FastAPI application entry
        ├── 📄 config.py                  # Pydantic Settings
        ├── 📄 exceptions.py              # Exception hierarchy
        ├── 📄 constants.py               # Application constants
        │
        ├── 📁 api/                       # HTTP layer (presentation)
        │   ├── 📄 __init__.py
        │   ├── 📄 app.py                 # FastAPI app factory
        │   ├── 📄 deps.py                # Dependency injection
        │   ├── 📄 middleware.py          # Custom middleware
        │   └── 📁 routes/                # Route handlers
        │       ├── 📄 __init__.py
        │       ├── 📄 health.py          # Health check endpoints
        │       ├── 📄 articles.py        # Article CRUD
        │       ├── 📄 stories.py         # Story management
        │       ├── 📄 editions.py        # Edition management
        │       ├── 📄 sources.py         # Source management
        │       ├── 📄 pipeline.py        # Pipeline triggers
        │       └── 📄 webhooks.py        # Webhook handlers
        │
        ├── 📁 services/                  # Application layer (use cases)
        │   ├── 📄 __init__.py
        │   ├── 📄 article_service.py     # Article operations
        │   ├── 📄 story_service.py       # Story operations
        │   ├── 📄 edition_service.py     # Edition operations
        │   ├── 📄 source_service.py      # Source operations
        │   ├── 📄 analysis_service.py    # Analysis orchestration
        │   └── 📄 publishing_service.py  # Newsletter publishing
        │
        ├── 📁 core/                      # Domain layer (business logic)
        │   ├── 📄 __init__.py
        │   ├── 📁 pipeline/              # Pipeline orchestration
        │   │   ├── 📄 __init__.py
        │   │   ├── 📄 orchestrator.py    # Main pipeline orchestrator
        │   │   ├── 📄 pass1.py           # Pass 1: Foundation
        │   │   ├── 📄 pass2.py           # Pass 2: Core Analysis
        │   │   ├── 📄 pass3.py           # Pass 3: Verification
        │   │   ├── 📄 pass4.py           # Pass 4: Production
        │   │   └── 📄 debate.py          # Debate protocol
        │   ├── 📁 quality/               # Quality systems
        │   │   ├── 📄 __init__.py
        │   │   ├── 📄 gates.py           # Quality gates
        │   │   ├── 📄 scoring.py         # Quality scoring
        │   │   ├── 📄 evaluators.py      # Dimension evaluators
        │   │   └── 📄 escalation.py      # Human escalation
        │   └── 📁 selection/             # Story selection
        │       ├── 📄 __init__.py
        │       ├── 📄 scorer.py          # Story scoring
        │       └── 📄 selector.py        # Story selection logic
        │
        ├── 📁 agents/                    # AI agents (domain)
        │   ├── 📄 __init__.py            # Public agent exports
        │   ├── 📄 base.py                # BaseAgent abstract class
        │   ├── 📄 result.py              # AgentResult, AgentMetadata
        │   ├── 📄 validation.py          # Output validation
        │   ├── 📁 collection/            # Collection agents
        │   │   ├── 📄 __init__.py
        │   │   ├── 📄 zone_scout.py      # Zone monitoring
        │   │   ├── 📄 story_scorer.py    # Story scoring
        │   │   └── 📄 source_aggregator.py
        │   ├── 📁 analysis/              # Analysis agents
        │   │   ├── 📄 __init__.py
        │   │   ├── 📄 factual.py         # Factual reconstruction
        │   │   ├── 📄 context.py         # Context building
        │   │   ├── 📄 actors.py          # Actor profiling
        │   │   ├── 📄 motivation.py      # Motivation analysis
        │   │   ├── 📄 chains.py          # Chain mapping
        │   │   ├── 📄 subtlety.py        # Subtlety analysis
        │   │   ├── 📄 theory.py          # Theory application
        │   │   ├── 📄 history.py         # Historical parallels
        │   │   └── 📄 geography.py       # Geographic analysis
        │   ├── 📁 adversarial/           # Adversarial agents
        │   │   ├── 📄 __init__.py
        │   │   ├── 📄 advocate.py        # Debate advocate
        │   │   ├── 📄 challenger.py      # Debate challenger
        │   │   ├── 📄 judge.py           # Debate judge
        │   │   ├── 📄 fact_checker.py    # Fact checking
        │   │   └── 📄 source_verifier.py # Source verification
        │   ├── 📁 production/            # Production agents
        │   │   ├── 📄 __init__.py
        │   │   ├── 📄 writer.py          # Article writer
        │   │   ├── 📄 voice.py           # Voice calibration
        │   │   ├── 📄 critic.py          # Self-critique
        │   │   └── 📄 preamble.py        # Preamble writer
        │   └── 📁 shared/                # Shared agent utilities
        │       ├── 📄 __init__.py
        │       ├── 📄 prompts.py         # Prompt loading
        │       └── 📄 parsing.py         # Output parsing utilities
        │
        ├── 📁 llm/                       # LLM infrastructure
        │   ├── 📄 __init__.py
        │   ├── 📄 router.py              # Model routing
        │   ├── 📄 tiers.py               # Model tier definitions
        │   ├── 📄 costs.py               # Cost tracking
        │   ├── 📄 cache.py               # Response caching
        │   ├── 📄 retry.py               # Retry logic
        │   └── 📁 providers/             # LLM providers
        │       ├── 📄 __init__.py
        │       ├── 📄 base.py            # Provider interface
        │       ├── 📄 anthropic.py       # Anthropic implementation
        │       └── 📄 openai.py          # OpenAI implementation
        │
        ├── 📁 rag/                       # RAG system
        │   ├── 📄 __init__.py
        │   ├── 📄 retriever.py           # Retrieval orchestration
        │   ├── 📄 embeddings.py          # Embedding generation
        │   ├── 📄 reranker.py            # Cross-encoder reranking
        │   ├── 📄 verification.py        # Source verification
        │   └── 📁 stores/                # Vector stores
        │       ├── 📄 __init__.py
        │       └── 📄 pgvector.py        # pgvector implementation
        │
        ├── 📁 ingestion/                 # Content ingestion
        │   ├── 📄 __init__.py
        │   ├── 📁 fetchers/              # Source fetchers
        │   │   ├── 📄 __init__.py
        │   │   ├── 📄 base.py            # Fetcher interface
        │   │   ├── 📄 rss.py             # RSS fetcher
        │   │   ├── 📄 api.py             # API fetcher
        │   │   └── 📄 scraper.py         # Web scraper
        │   └── 📁 processors/            # Content processors
        │       ├── 📄 __init__.py
        │       ├── 📄 extractor.py       # Content extraction
        │       ├── 📄 deduplicator.py    # Deduplication
        │       └── 📄 normalizer.py      # Normalization
        │
        ├── 📁 models/                    # Database models (infrastructure)
        │   ├── 📄 __init__.py            # Model exports
        │   ├── 📄 base.py                # Base model class
        │   ├── 📄 source.py              # Source model
        │   ├── 📄 article.py             # Article model
        │   ├── 📄 story.py               # Story model
        │   ├── 📄 edition.py             # Edition model
        │   ├── 📄 analysis.py            # Analysis result models
        │   └── 📄 audit.py               # Audit log model
        │
        ├── 📁 schemas/                   # Pydantic schemas
        │   ├── 📄 __init__.py            # Schema exports
        │   ├── 📄 base.py                # Base schemas
        │   ├── 📄 source.py              # Source schemas
        │   ├── 📄 article.py             # Article schemas
        │   ├── 📄 story.py               # Story schemas
        │   ├── 📄 edition.py             # Edition schemas
        │   ├── 📄 analysis.py            # Analysis schemas
        │   ├── 📁 agents/                # Agent-specific schemas
        │   │   ├── 📄 __init__.py
        │   │   ├── 📄 motivation.py      # Motivation I/O schemas
        │   │   ├── 📄 chains.py          # Chain I/O schemas
        │   │   └── 📄 debate.py          # Debate I/O schemas
        │   └── 📁 api/                   # API request/response schemas
        │       ├── 📄 __init__.py
        │       ├── 📄 requests.py        # Request schemas
        │       └── 📄 responses.py       # Response schemas
        │
        ├── 📁 repositories/              # Data access layer
        │   ├── 📄 __init__.py
        │   ├── 📄 base.py                # Generic repository
        │   ├── 📄 source.py              # Source repository
        │   ├── 📄 article.py             # Article repository
        │   ├── 📄 story.py               # Story repository
        │   └── 📄 edition.py             # Edition repository
        │
        ├── 📁 tasks/                     # Celery tasks
        │   ├── 📄 __init__.py
        │   ├── 📄 celery.py              # Celery app configuration
        │   ├── 📄 ingestion.py           # Ingestion tasks
        │   ├── 📄 analysis.py            # Analysis tasks
        │   ├── 📄 pipeline.py            # Pipeline tasks
        │   ├── 📄 publishing.py          # Publishing tasks
        │   └── 📄 maintenance.py         # Maintenance tasks
        │
        ├── 📁 infrastructure/            # External integrations
        │   ├── 📄 __init__.py
        │   ├── 📄 database.py            # Database connection
        │   ├── 📄 redis.py               # Redis connection
        │   ├── 📄 s3.py                  # S3 client
        │   └── 📄 email.py               # Email service
        │
        └── 📁 utils/                     # Shared utilities
            ├── 📄 __init__.py
            ├── 📄 logging.py             # Structured logging setup
            ├── 📄 metrics.py             # Prometheus metrics
            ├── 📄 datetime.py            # Date/time utilities
            ├── 📄 hashing.py             # Hashing utilities
            └── 📄 validation.py          # Validation helpers
```

---

# LAYER RESPONSIBILITIES

## Presentation Layer (`api/`)

**Purpose**: HTTP request/response handling ONLY

```python
# ✅ ALLOWED in api/
- HTTP request parsing
- Input validation (via Pydantic schemas)
- Output serialization
- HTTP error handling
- Authentication/authorization checks
- Rate limiting

# ❌ FORBIDDEN in api/
- Business logic
- Database queries
- LLM calls
- Complex computations
```

## Application Layer (`services/`)

**Purpose**: Orchestrate use cases, coordinate domain objects

```python
# ✅ ALLOWED in services/
- Transaction management
- Orchestrating multiple domain operations
- Business rule enforcement
- Calling repositories
- Calling domain services/agents
- Event publishing

# ❌ FORBIDDEN in services/
- HTTP concerns
- Direct database queries (use repositories)
- Direct LLM calls (use agents)
```

## Domain Layer (`core/`, `agents/`)

**Purpose**: Business logic and AI agents

```python
# ✅ ALLOWED in core/ and agents/
- Business logic
- Domain models
- Agent implementations
- Quality assessment
- Pipeline orchestration

# ❌ FORBIDDEN in core/ and agents/
- Database queries (use repositories)
- HTTP concerns
- Infrastructure details
```

## Infrastructure Layer (`models/`, `llm/`, `repositories/`, `infrastructure/`)

**Purpose**: External system integrations

```python
# ✅ ALLOWED in infrastructure/
- Database models and queries
- LLM provider clients
- External API clients
- File storage
- Email services

# ❌ FORBIDDEN in infrastructure/
- Business logic
- Domain rules
```

---

# MODULE PUBLIC INTERFACES

Each module MUST have a single `__init__.py` that exports its public API:

```python
# src/undertow/agents/__init__.py
"""
Public interface for agents module.

ONLY classes/functions listed here are public API.
"""
from undertow.agents.base import BaseAgent, AgentResult, AgentMetadata
from undertow.agents.analysis import (
    MotivationAnalysisAgent,
    ChainMappingAgent,
    SubtletyAnalysisAgent,
)
from undertow.agents.adversarial import (
    AdvocateAgent,
    ChallengerAgent,
    JudgeAgent,
)
from undertow.agents.production import (
    ArticleWriterAgent,
    VoiceCalibrationAgent,
)

__all__ = [
    # Base
    "BaseAgent",
    "AgentResult",
    "AgentMetadata",
    # Analysis
    "MotivationAnalysisAgent",
    "ChainMappingAgent",
    "SubtletyAnalysisAgent",
    # Adversarial
    "AdvocateAgent",
    "ChallengerAgent",
    "JudgeAgent",
    # Production
    "ArticleWriterAgent",
    "VoiceCalibrationAgent",
]
```

---

# IMPORT RULES

## Allowed Import Patterns

```python
# ✅ CORRECT: Import from public interface
from undertow.agents import MotivationAnalysisAgent
from undertow.services import ArticleService
from undertow.schemas import ArticleCreate

# ✅ CORRECT: Type checking imports
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from undertow.services import ArticleService
```

## Forbidden Import Patterns

```python
# ❌ FORBIDDEN: Import internal modules
from undertow.agents.analysis.motivation import _internal_helper
from undertow.services.article_service import ArticleService  # Should use __init__.py

# ❌ FORBIDDEN: Relative imports
from ..utils import helper
from .internal import something

# ❌ FORBIDDEN: Wildcard imports
from undertow.agents import *

# ❌ FORBIDDEN: Cross-layer violations
# In agents/:
from undertow.api import router  # agents cannot import api
from undertow.services import ArticleService  # agents cannot import services
```

---

# CONFIGURATION FILES

## pyproject.toml

```toml
[tool.poetry]
name = "the-undertow"
version = "1.0.0"
description = "AI-powered geopolitical intelligence system"
authors = ["The Undertow Team"]
readme = "README.md"
packages = [{include = "undertow", from = "src"}]

[tool.poetry.dependencies]
python = "^3.11"

# Web framework
fastapi = "^0.109.0"
uvicorn = {extras = ["standard"], version = "^0.27.0"}
pydantic = "^2.5.0"
pydantic-settings = "^2.1.0"

# Database
sqlalchemy = {extras = ["asyncio"], version = "^2.0.0"}
asyncpg = "^0.29.0"
alembic = "^1.13.0"
pgvector = "^0.2.0"

# Task queue
celery = {extras = ["redis"], version = "^5.3.0"}
redis = "^5.0.0"

# AI
anthropic = "^0.18.0"
openai = "^1.10.0"
langchain = "^0.1.0"
sentence-transformers = "^2.2.0"

# Utilities
httpx = "^0.26.0"
structlog = "^24.1.0"
tenacity = "^8.2.0"
feedparser = "^6.0.0"
trafilatura = "^1.6.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
pytest-asyncio = "^0.23.0"
pytest-cov = "^4.1.0"
hypothesis = "^6.92.0"
factory-boy = "^3.3.0"
ruff = "^0.1.9"
mypy = "^1.8.0"
pre-commit = "^3.6.0"
import-linter = "^2.0"
interrogate = "^1.5.0"
bandit = "^1.7.0"
radon = "^6.0.0"

[tool.ruff]
target-version = "py311"
line-length = 100
select = ["E", "W", "F", "I", "B", "C4", "UP", "ARG", "SIM", "TCH", "PTH", "ERA", "PL", "RUF"]

[tool.ruff.isort]
known-first-party = ["undertow"]

[tool.mypy]
python_version = "3.11"
strict = true
plugins = ["pydantic.mypy"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = "-ra --strict-markers"

[tool.coverage.run]
source = ["src/undertow"]
branch = true

[tool.coverage.report]
fail_under = 85

[tool.importlinter]
root_package = "undertow"

[[tool.importlinter.contracts]]
name = "Layers"
type = "layers"
layers = [
    "undertow.api",
    "undertow.services",
    "undertow.core",
    "undertow.agents",
]

[[tool.importlinter.contracts]]
name = "Agents isolation"
type = "forbidden"
source_modules = ["undertow.agents"]
forbidden_modules = ["undertow.api", "undertow.services"]
```

## .pre-commit-config.yaml

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [pydantic>=2.0, types-redis]

  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.7
    hooks:
      - id: bandit
        args: ["-c", "pyproject.toml"]

  - repo: https://github.com/seddonym/import-linter
    rev: v2.0
    hooks:
      - id: import-linter

  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets

  - repo: https://github.com/commitizen-tools/commitizen
    rev: v3.13.0
    hooks:
      - id: commitizen
        stages: [commit-msg]
```

---

# MAKEFILE

```makefile
.PHONY: help install dev test lint format check clean docker-up docker-down

help:
	@echo "Available commands:"
	@echo "  install     Install production dependencies"
	@echo "  dev         Install development dependencies"
	@echo "  test        Run all tests"
	@echo "  lint        Run linters"
	@echo "  format      Format code"
	@echo "  check       Run all checks (lint + test)"
	@echo "  clean       Clean build artifacts"
	@echo "  docker-up   Start development stack"
	@echo "  docker-down Stop development stack"

install:
	poetry install --only main

dev:
	poetry install
	pre-commit install

test:
	poetry run pytest tests/ -v --cov=src/undertow --cov-report=term-missing

test-unit:
	poetry run pytest tests/unit -v

test-integration:
	poetry run pytest tests/integration -v

lint:
	poetry run ruff check src/ tests/
	poetry run mypy src/
	poetry run lint-imports
	poetry run bandit -r src/ -c pyproject.toml
	poetry run interrogate src/ --fail-under 100

format:
	poetry run ruff format src/ tests/
	poetry run ruff check --fix src/ tests/

check: lint test

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf .coverage htmlcov/

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

migrate:
	poetry run alembic upgrade head

migrate-create:
	poetry run alembic revision --autogenerate -m "$(name)"

run:
	poetry run uvicorn undertow.main:app --reload --host 0.0.0.0 --port 8000

worker:
	poetry run celery -A undertow.tasks.celery worker -l info

beat:
	poetry run celery -A undertow.tasks.celery beat -l info
```

---

# DOCKER COMPOSE

```yaml
# docker-compose.yml
version: "3.9"

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile.dev
    ports:
      - "8000:8000"
    volumes:
      - ./src:/app/src
      - ./tests:/app/tests
    environment:
      - DATABASE_URL=postgresql+asyncpg://undertow:undertow@db:5432/undertow
      - REDIS_URL=redis://redis:6379/0
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    depends_on:
      - db
      - redis
    command: uvicorn undertow.main:app --reload --host 0.0.0.0 --port 8000

  worker:
    build:
      context: .
      dockerfile: Dockerfile.dev
    volumes:
      - ./src:/app/src
    environment:
      - DATABASE_URL=postgresql+asyncpg://undertow:undertow@db:5432/undertow
      - REDIS_URL=redis://redis:6379/0
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    depends_on:
      - db
      - redis
    command: celery -A undertow.tasks.celery worker -l info

  beat:
    build:
      context: .
      dockerfile: Dockerfile.dev
    volumes:
      - ./src:/app/src
    environment:
      - DATABASE_URL=postgresql+asyncpg://undertow:undertow@db:5432/undertow
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    command: celery -A undertow.tasks.celery beat -l info

  db:
    image: pgvector/pgvector:pg15
    environment:
      POSTGRES_USER: undertow
      POSTGRES_PASSWORD: undertow
      POSTGRES_DB: undertow
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

---

# FILE NAMING CONVENTIONS

| Type | Convention | Example |
|------|------------|---------|
| Modules | snake_case | `article_service.py` |
| Classes | PascalCase | `ArticleService` |
| Functions | snake_case | `get_article` |
| Constants | SCREAMING_SNAKE | `MAX_RETRIES` |
| Type aliases | PascalCase | `ArticleDict` |
| Test files | test_*.py | `test_article_service.py` |
| Migration files | NNNN_description.py | `0001_initial_schema.py` |
| Prompt files | name_vN.txt | `motivation_v2.txt` |

---

# QUICK SETUP

```bash
# 1. Clone repository
git clone https://github.com/org/the-undertow.git
cd the-undertow

# 2. Install dependencies
make dev

# 3. Set up environment
cp .env.example .env
# Edit .env with your API keys

# 4. Start services
make docker-up

# 5. Run migrations
make migrate

# 6. Start development server
make run

# In another terminal, start worker
make worker
```

---

*This structure follows Python best practices, clean architecture principles, and is optimized for multi-agent AI systems.*

