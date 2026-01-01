# The Undertow — Implementation Plan

## Python-First Architecture with Production-Grade Infrastructure

---

# EXECUTIVE SUMMARY

This plan details a **16-week implementation** of The Undertow system using Python as the primary language, with supporting technologies for frontend, infrastructure, and specialized components.

**Target Launch:** MVP with full 4-pass pipeline, 5 daily articles, operational quality gates

---

# SECTION 1: TECHNOLOGY STACK

## 1.1 Core Stack Decision Matrix

| Layer | Technology | Rationale |
|-------|------------|-----------|
| **Backend API** | Python + FastAPI | Async-native, excellent typing, OpenAPI auto-docs |
| **Task Queue** | Celery + Redis | Battle-tested for long-running AI tasks |
| **Database** | PostgreSQL 15 | JSONB for flexible schemas, full-text search |
| **Vector DB** | Pinecone / pgvector | Embeddings for RAG (pgvector for cost control) |
| **Cache** | Redis | Session, response cache, rate limiting |
| **AI Orchestration** | LangChain / LangGraph | Agent orchestration, prompt management |
| **Frontend** | Next.js 14 (React) | SSR, excellent DX, Vercel deployment |
| **Admin UI** | React + Tailwind | Shared components with frontend |
| **Email** | SendGrid + MJML | Reliable delivery, responsive templates |
| **Monitoring** | Prometheus + Grafana | Metrics, alerting, dashboards |
| **Logging** | Structlog + Loki | Structured JSON logs, searchable |
| **CI/CD** | GitHub Actions | Integrated with repo, good Python support |
| **Infrastructure** | Docker + AWS (ECS) | Or Railway/Render for simpler deploys |

---

## 1.2 Python Package Architecture

```
undertow/
├── pyproject.toml              # Modern Python packaging (Poetry/PDM)
├── .env.example
├── docker-compose.yml
├── Dockerfile
│
├── src/
│   └── undertow/
│       ├── __init__.py
│       ├── main.py             # FastAPI app entry
│       ├── config.py           # Pydantic Settings
│       │
│       ├── api/                # FastAPI routes
│       │   ├── __init__.py
│       │   ├── routes/
│       │   │   ├── articles.py
│       │   │   ├── candidates.py
│       │   │   ├── editions.py
│       │   │   ├── pipeline.py
│       │   │   ├── reviews.py
│       │   │   ├── sources.py
│       │   │   └── admin.py
│       │   ├── deps.py         # Dependency injection
│       │   └── middleware.py
│       │
│       ├── core/               # Core business logic
│       │   ├── __init__.py
│       │   ├── pipeline/
│       │   │   ├── orchestrator.py
│       │   │   ├── pass1.py
│       │   │   ├── pass2.py
│       │   │   ├── pass3.py
│       │   │   └── pass4.py
│       │   ├── quality/
│       │   │   ├── gates.py
│       │   │   ├── evaluator.py
│       │   │   └── escalation.py
│       │   └── selection/
│       │       ├── scorer.py
│       │       └── selector.py
│       │
│       ├── agents/             # AI Agents
│       │   ├── __init__.py
│       │   ├── base.py         # Base agent class
│       │   ├── collection/
│       │   │   ├── zone_scout.py
│       │   │   └── story_scorer.py
│       │   ├── analysis/
│       │   │   ├── factual.py
│       │   │   ├── context.py
│       │   │   ├── motivation.py
│       │   │   ├── chains.py
│       │   │   └── subtlety.py
│       │   ├── adversarial/
│       │   │   ├── advocate.py
│       │   │   ├── challenger.py
│       │   │   ├── judge.py
│       │   │   └── fact_checker.py
│       │   └── production/
│       │       ├── writer.py
│       │       ├── voice.py
│       │       └── preamble.py
│       │
│       ├── llm/                # LLM abstraction layer
│       │   ├── __init__.py
│       │   ├── providers/
│       │   │   ├── base.py
│       │   │   ├── openai.py
│       │   │   └── anthropic.py
│       │   ├── router.py       # Model routing logic
│       │   ├── costs.py        # Cost tracking
│       │   └── cache.py        # Response caching
│       │
│       ├── rag/                # RAG system
│       │   ├── __init__.py
│       │   ├── embeddings.py
│       │   ├── retriever.py
│       │   ├── reranker.py
│       │   └── query_expansion.py
│       │
│       ├── ingestion/          # Source ingestion
│       │   ├── __init__.py
│       │   ├── fetchers/
│       │   │   ├── rss.py
│       │   │   ├── api.py
│       │   │   └── scraper.py
│       │   ├── processors/
│       │   │   ├── extractor.py
│       │   │   ├── classifier.py
│       │   │   └── entity.py
│       │   └── scheduler.py
│       │
│       ├── models/             # SQLAlchemy models
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── source.py
│       │   ├── article.py
│       │   ├── story.py
│       │   ├── edition.py
│       │   └── user.py
│       │
│       ├── schemas/            # Pydantic schemas
│       │   ├── __init__.py
│       │   ├── source.py
│       │   ├── article.py
│       │   ├── story.py
│       │   ├── analysis.py
│       │   └── responses.py
│       │
│       ├── services/           # Business services
│       │   ├── __init__.py
│       │   ├── source_service.py
│       │   ├── article_service.py
│       │   ├── story_service.py
│       │   ├── edition_service.py
│       │   └── notification_service.py
│       │
│       ├── tasks/              # Celery tasks
│       │   ├── __init__.py
│       │   ├── celery_app.py
│       │   ├── ingestion.py
│       │   ├── analysis.py
│       │   ├── production.py
│       │   └── scheduled.py
│       │
│       └── utils/
│           ├── __init__.py
│           ├── logging.py
│           ├── metrics.py
│           └── helpers.py
│
├── tests/
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── prompts/                    # Prompt templates (version controlled)
│   ├── collection/
│   ├── analysis/
│   ├── adversarial/
│   └── production/
│
├── migrations/                 # Alembic migrations
│   └── versions/
│
└── scripts/
    ├── seed_sources.py
    ├── backfill_embeddings.py
    └── run_pipeline.py
```

---

## 1.3 Key Python Dependencies

```toml
# pyproject.toml

[project]
name = "undertow"
version = "1.0.0"
requires-python = ">=3.11"

dependencies = [
    # Web Framework
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    
    # Database
    "sqlalchemy>=2.0.25",
    "asyncpg>=0.29.0",           # Async PostgreSQL
    "alembic>=1.13.0",
    "pgvector>=0.2.4",           # Vector similarity
    
    # Task Queue
    "celery[redis]>=5.3.0",
    "redis>=5.0.0",
    "flower>=2.0.0",             # Celery monitoring
    
    # AI/LLM
    "openai>=1.10.0",
    "anthropic>=0.18.0",
    "langchain>=0.1.0",
    "langchain-openai>=0.0.5",
    "langchain-anthropic>=0.1.0",
    "langgraph>=0.0.20",
    "tiktoken>=0.5.0",           # Token counting
    
    # RAG
    "sentence-transformers>=2.3.0",
    "pinecone-client>=3.0.0",
    "rank-bm25>=0.2.2",          # Sparse retrieval
    
    # Content Processing
    "beautifulsoup4>=4.12.0",
    "feedparser>=6.0.0",
    "trafilatura>=1.6.0",        # Article extraction
    "spacy>=3.7.0",              # NER
    "langdetect>=1.0.9",
    
    # HTTP
    "httpx>=0.26.0",
    "aiohttp>=3.9.0",
    
    # Utilities
    "structlog>=24.1.0",
    "python-jose[cryptography]>=3.3.0",  # JWT
    "passlib[bcrypt]>=1.7.4",
    "python-multipart>=0.0.6",
    "tenacity>=8.2.0",           # Retries
    "cachetools>=5.3.0",
    
    # Monitoring
    "prometheus-client>=0.19.0",
    "sentry-sdk[fastapi]>=1.39.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "httpx>=0.26.0",             # Test client
    "factory-boy>=3.3.0",
    "faker>=22.0.0",
    "mypy>=1.8.0",
    "ruff>=0.1.0",
    "pre-commit>=3.6.0",
]
```

---

# SECTION 2: DEVELOPMENT PHASES

## Phase Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        16-WEEK IMPLEMENTATION TIMELINE                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PHASE 1: FOUNDATION (Weeks 1-4)                                           │
│  ├── Week 1-2: Infrastructure & Core Models                                │
│  └── Week 3-4: Ingestion Pipeline & Source Management                      │
│                                                                             │
│  PHASE 2: INTELLIGENCE (Weeks 5-9)                                         │
│  ├── Week 5-6: LLM Abstraction & Agent Framework                           │
│  ├── Week 7-8: Pass 1 & Pass 2 Implementation                              │
│  └── Week 9: Pass 3 Adversarial System                                     │
│                                                                             │
│  PHASE 3: PRODUCTION (Weeks 10-12)                                         │
│  ├── Week 10: Pass 4 & Article Generation                                  │
│  ├── Week 11: Newsletter Assembly & Delivery                               │
│  └── Week 12: Quality Gates & Human Review                                 │
│                                                                             │
│  PHASE 4: POLISH (Weeks 13-16)                                             │
│  ├── Week 13: Admin Dashboard                                              │
│  ├── Week 14: Monitoring & Alerting                                        │
│  ├── Week 15: Testing & Bug Fixes                                          │
│  └── Week 16: Deployment & Launch Prep                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Foundation (Weeks 1-4)

### Week 1-2: Infrastructure & Core Models

**Deliverables:**
- [ ] Project scaffolding with Poetry/PDM
- [ ] Docker Compose for local development
- [ ] PostgreSQL + Redis setup
- [ ] FastAPI app with health checks
- [ ] SQLAlchemy models (all entities)
- [ ] Alembic migrations
- [ ] Pydantic schemas
- [ ] Basic CRUD endpoints for Sources
- [ ] Authentication (JWT)
- [ ] GitHub Actions CI pipeline

**Code Focus:**

```python
# src/undertow/models/source.py
from sqlalchemy import Column, String, Integer, Boolean, DateTime, JSON, Enum
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from src.undertow.models.base import Base
import uuid

class Source(Base):
    __tablename__ = "sources"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    url = Column(String(500), nullable=False, unique=True)
    type = Column(Enum("RSS", "API", "SCRAPER", name="source_type"), nullable=False)
    tier = Column(Integer, nullable=False)  # 1-4
    zones = Column(ARRAY(String), nullable=False, default=[])
    languages = Column(ARRAY(String), nullable=False, default=["en"])
    reliability_score = Column(Float, default=0.5)
    bias_indicators = Column(JSON, default={})
    refresh_interval_minutes = Column(Integer, default=60)
    active = Column(Boolean, default=True)
    last_fetch_at = Column(DateTime(timezone=True))
    last_fetch_status = Column(String(20))
    consecutive_failures = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

```python
# src/undertow/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # App
    app_env: str = "development"
    app_secret: str
    debug: bool = False
    
    # Database
    database_url: str
    database_pool_size: int = 20
    
    # Redis
    redis_url: str
    
    # AI Providers
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    ai_provider_preference: str = "ANTHROPIC"
    
    # Budget
    daily_budget_limit: float = 50.0
    
    class Config:
        env_file = ".env"

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

### Week 3-4: Ingestion Pipeline & Source Management

**Deliverables:**
- [ ] RSS feed fetcher
- [ ] Web scraper (Trafilatura-based)
- [ ] Article processor (extraction, cleaning)
- [ ] Language detection
- [ ] Zone classification (rule-based + LLM)
- [ ] Entity extraction (spaCy NER)
- [ ] Embedding generation
- [ ] Celery tasks for async ingestion
- [ ] Source health monitoring
- [ ] Admin endpoints for source management

**Code Focus:**

```python
# src/undertow/ingestion/fetchers/rss.py
import feedparser
import httpx
from datetime import datetime
from typing import AsyncGenerator
from src.undertow.schemas.article import RawArticle

class RSSFetcher:
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        
    async def fetch(self, url: str) -> AsyncGenerator[RawArticle, None]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            
        feed = feedparser.parse(response.text)
        
        for entry in feed.entries:
            yield RawArticle(
                url=entry.link,
                title=entry.title,
                summary=entry.get("summary", ""),
                published_at=self._parse_date(entry.get("published")),
                source_url=url
            )
    
    def _parse_date(self, date_str: str | None) -> datetime | None:
        if not date_str:
            return None
        # Parse various date formats...
```

```python
# src/undertow/ingestion/processors/extractor.py
import trafilatura
from src.undertow.schemas.article import ExtractedArticle

class ArticleExtractor:
    async def extract(self, url: str, html: str | None = None) -> ExtractedArticle:
        if html is None:
            downloaded = trafilatura.fetch_url(url)
        else:
            downloaded = html
            
        if not downloaded:
            raise ExtractionError(f"Could not fetch {url}")
            
        content = trafilatura.extract(
            downloaded,
            include_comments=False,
            include_tables=True,
            no_fallback=False,
            favor_precision=True
        )
        
        metadata = trafilatura.extract_metadata(downloaded)
        
        return ExtractedArticle(
            url=url,
            title=metadata.title if metadata else None,
            content=content,
            author=metadata.author if metadata else None,
            published_at=metadata.date if metadata else None,
            language=self._detect_language(content)
        )
```

```python
# src/undertow/tasks/ingestion.py
from celery import shared_task
from src.undertow.services.article_service import ArticleService
from src.undertow.ingestion.fetchers.rss import RSSFetcher

@shared_task(bind=True, max_retries=3)
def fetch_source(self, source_id: str):
    """Fetch articles from a single source."""
    try:
        source = SourceService.get(source_id)
        fetcher = get_fetcher(source.type)
        
        articles = []
        async for raw_article in fetcher.fetch(source.url):
            # Check if already exists
            if not ArticleService.exists(raw_article.url):
                processed = await process_article(raw_article)
                articles.append(processed)
        
        ArticleService.bulk_create(articles)
        SourceService.update_fetch_status(source_id, "SUCCESS")
        
    except Exception as e:
        SourceService.update_fetch_status(source_id, "FAILED")
        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))
```

---

## Phase 2: Intelligence (Weeks 5-9)

### Week 5-6: LLM Abstraction & Agent Framework

**Deliverables:**
- [ ] LLM provider abstraction layer
- [ ] Model router (tier-based)
- [ ] Cost tracker
- [ ] Response caching
- [ ] Token counting & limits
- [ ] Retry logic with backoff
- [ ] Base Agent class
- [ ] Prompt template system
- [ ] Agent output validation

**Code Focus:**

```python
# src/undertow/llm/providers/base.py
from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import AsyncGenerator

class LLMResponse(BaseModel):
    content: str
    input_tokens: int
    output_tokens: int
    model: str
    latency_ms: int

class BaseLLMProvider(ABC):
    @abstractmethod
    async def complete(
        self,
        messages: list[dict],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: dict | None = None
    ) -> LLMResponse:
        pass
    
    @abstractmethod
    async def stream(
        self,
        messages: list[dict],
        model: str,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        pass
```

```python
# src/undertow/llm/providers/anthropic.py
import anthropic
import time
from src.undertow.llm.providers.base import BaseLLMProvider, LLMResponse

class AnthropicProvider(BaseLLMProvider):
    def __init__(self, api_key: str):
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        
    async def complete(
        self,
        messages: list[dict],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: dict | None = None
    ) -> LLMResponse:
        start = time.perf_counter()
        
        # Convert messages to Anthropic format
        system = next((m["content"] for m in messages if m["role"] == "system"), None)
        chat_messages = [m for m in messages if m["role"] != "system"]
        
        response = await self.client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=chat_messages
        )
        
        latency = int((time.perf_counter() - start) * 1000)
        
        return LLMResponse(
            content=response.content[0].text,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            model=model,
            latency_ms=latency
        )
```

```python
# src/undertow/llm/router.py
from src.undertow.config import get_settings
from src.undertow.llm.providers.openai import OpenAIProvider
from src.undertow.llm.providers.anthropic import AnthropicProvider

class ModelRouter:
    """Routes tasks to appropriate models based on tier and provider preference."""
    
    TIER_MODELS = {
        "openai": {
            "frontier": "gpt-4o",
            "high": "gpt-4o",
            "standard": "gpt-4o-mini",
            "fast": "gpt-4o-mini"
        },
        "anthropic": {
            "frontier": "claude-sonnet-4-20250514",
            "high": "claude-sonnet-4-20250514",
            "standard": "claude-sonnet-4-20250514",
            "fast": "claude-3-haiku-20240307"
        }
    }
    
    TASK_TIERS = {
        "zone_scout": "fast",
        "story_scorer": "standard",
        "factual_reconstruction": "standard",
        "motivation_analysis": "frontier",
        "chain_analysis": "frontier",
        "debate_advocate": "frontier",
        "debate_challenger": "frontier",
        "article_writer": "frontier",
        # ... etc
    }
    
    def __init__(self):
        settings = get_settings()
        self.preference = settings.ai_provider_preference.lower()
        
        self.providers = {}
        if settings.openai_api_key:
            self.providers["openai"] = OpenAIProvider(settings.openai_api_key)
        if settings.anthropic_api_key:
            self.providers["anthropic"] = AnthropicProvider(settings.anthropic_api_key)
    
    def get_model_for_task(self, task_name: str) -> tuple[str, str]:
        """Returns (provider, model) for a given task."""
        tier = self.TASK_TIERS.get(task_name, "standard")
        provider = self.preference
        
        if provider not in self.providers:
            provider = list(self.providers.keys())[0]
            
        model = self.TIER_MODELS[provider][tier]
        return provider, model
    
    async def complete(self, task_name: str, messages: list[dict], **kwargs):
        """Complete a task using the appropriate model."""
        provider_name, model = self.get_model_for_task(task_name)
        provider = self.providers[provider_name]
        
        response = await provider.complete(messages, model, **kwargs)
        
        # Track costs
        await self._track_cost(task_name, provider_name, model, response)
        
        return response
```

```python
# src/undertow/agents/base.py
from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import TypeVar, Generic
from src.undertow.llm.router import ModelRouter

T = TypeVar("T", bound=BaseModel)

class BaseAgent(ABC, Generic[T]):
    """Base class for all analysis agents."""
    
    task_name: str  # Override in subclass
    
    def __init__(self, router: ModelRouter):
        self.router = router
        self.prompt_template = self._load_prompt()
    
    def _load_prompt(self) -> str:
        """Load prompt from prompts/ directory."""
        path = f"prompts/{self.task_name}.txt"
        with open(path) as f:
            return f.read()
    
    @abstractmethod
    def _build_messages(self, context: dict) -> list[dict]:
        """Build messages for the LLM."""
        pass
    
    @abstractmethod
    def _parse_response(self, content: str) -> T:
        """Parse LLM response into typed output."""
        pass
    
    async def run(self, context: dict) -> T:
        """Execute the agent."""
        messages = self._build_messages(context)
        
        response = await self.router.complete(
            self.task_name,
            messages,
            response_format={"type": "json_object"}
        )
        
        return self._parse_response(response.content)
```

### Week 7-8: Pass 1 & Pass 2 Implementation

**Deliverables:**
- [ ] Story candidate generation
- [ ] Story scoring agent
- [ ] Factual reconstruction agent
- [ ] Context analysis agent
- [ ] Actor analysis agent
- [ ] Motivation analysis agent (4-layer)
- [ ] Chain mapping agent
- [ ] Subtlety analysis agent
- [ ] Pass 1 orchestrator
- [ ] Pass 2 orchestrator
- [ ] Quality gate checks

**Code Focus:**

```python
# src/undertow/agents/analysis/motivation.py
from pydantic import BaseModel, Field
from src.undertow.agents.base import BaseAgent

class AssessedFactor(BaseModel):
    assessment: str
    evidence: str
    confidence: float = Field(ge=0, le=1)

class MotivationLayer1(BaseModel):
    decision_maker: str
    political_position: AssessedFactor
    domestic_needs: AssessedFactor
    psychology_worldview: AssessedFactor
    personal_relationships: AssessedFactor
    legacy: AssessedFactor

class MotivationLayer2(BaseModel):
    foreign_ministry: AssessedFactor
    military_intelligence: AssessedFactor
    economic_actors: AssessedFactor
    institutional_momentum: AssessedFactor

class MotivationLayer3(BaseModel):
    systemic_position: AssessedFactor
    threat_environment: AssessedFactor
    economic_structure: AssessedFactor
    geographic_imperatives: AssessedFactor

class MotivationLayer4(BaseModel):
    what_changed: AssessedFactor
    position_shifts: AssessedFactor
    constraint_relaxed: AssessedFactor
    whats_coming: AssessedFactor
    convergence: AssessedFactor

class AlternativeHypothesis(BaseModel):
    hypothesis: str
    supporting_evidence: str
    weaknesses: str
    probability: float = Field(ge=0, le=1)

class MotivationSynthesis(BaseModel):
    primary_driver: dict
    enabling_conditions: list[str]
    alternative_hypotheses: list[AlternativeHypothesis]
    evidence_that_would_change: list[str]

class MotivationAnalysisOutput(BaseModel):
    layer1_individual: MotivationLayer1
    layer2_institutional: MotivationLayer2
    layer3_structural: MotivationLayer3
    layer4_window: MotivationLayer4
    synthesis: MotivationSynthesis

class MotivationAnalysisAgent(BaseAgent[MotivationAnalysisOutput]):
    task_name = "motivation_analysis"
    
    def _build_messages(self, context: dict) -> list[dict]:
        return [
            {"role": "system", "content": self.prompt_template},
            {"role": "user", "content": f"""
Analyze the motivations behind this event:

EVENT: {context['event_summary']}

FACTUAL RECONSTRUCTION:
{context['factual_reconstruction']}

KEY ACTORS:
{context['actors']}

CONTEXT:
{context['context_analysis']}

Provide your analysis in JSON format matching the required schema.
"""}
        ]
    
    def _parse_response(self, content: str) -> MotivationAnalysisOutput:
        import json
        data = json.loads(content)
        return MotivationAnalysisOutput(**data)
```

```python
# src/undertow/core/pipeline/pass2.py
from src.undertow.agents.analysis.motivation import MotivationAnalysisAgent
from src.undertow.agents.analysis.chains import ChainMappingAgent
from src.undertow.agents.analysis.subtlety import SubtletyAnalysisAgent
from src.undertow.core.quality.gates import QualityGate

class Pass2Orchestrator:
    """Orchestrates Pass 2: Core Analysis."""
    
    def __init__(self, router: ModelRouter):
        self.motivation_agent = MotivationAnalysisAgent(router)
        self.chain_agent = ChainMappingAgent(router)
        self.subtlety_agent = SubtletyAnalysisAgent(router)
        self.quality_gate = QualityGate("analysis", threshold=0.80)
    
    async def run(self, story: Story, pass1_output: Pass1Output) -> Pass2Output:
        context = self._build_context(story, pass1_output)
        
        # Run analyses (can parallelize some)
        motivation = await self.motivation_agent.run(context)
        
        # Chain analysis needs motivation context
        context["motivation_analysis"] = motivation
        chains = await self.chain_agent.run(context)
        
        # Subtlety can run in parallel with chains
        subtlety = await self.subtlety_agent.run(context)
        
        output = Pass2Output(
            motivation_analysis=motivation,
            chain_analysis=chains,
            subtlety_analysis=subtlety
        )
        
        # Quality gate check
        quality_score = await self.quality_gate.evaluate(output)
        
        if quality_score < self.quality_gate.threshold:
            # Trigger revision or escalation
            output = await self._revise_or_escalate(output, quality_score)
        
        return output
```

### Week 9: Pass 3 Adversarial System

**Deliverables:**
- [ ] Advocate agent
- [ ] Challenger agent
- [ ] Judge agent
- [ ] Debate orchestrator (3 rounds)
- [ ] Fact checker agent
- [ ] Source verification pipeline
- [ ] Pass 3 orchestrator
- [ ] Quality gate for adversarial

**Code Focus:**

```python
# src/undertow/core/pipeline/debate.py
from dataclasses import dataclass
from src.undertow.agents.adversarial.advocate import AdvocateAgent
from src.undertow.agents.adversarial.challenger import ChallengerAgent
from src.undertow.agents.adversarial.judge import JudgeAgent

@dataclass
class DebateRound:
    round_number: int
    advocate_defense: str
    challenges: list[dict]
    responses: list[dict]

class DebateOrchestrator:
    """Manages the 3-round adversarial debate."""
    
    def __init__(self, router: ModelRouter, rounds: int = 3):
        self.advocate = AdvocateAgent(router)
        self.challenger = ChallengerAgent(router)
        self.judge = JudgeAgent(router)
        self.rounds = rounds
    
    async def run_debate(self, analysis: dict) -> DebateResult:
        transcript = []
        
        for round_num in range(1, self.rounds + 1):
            # Advocate presents/defends
            if round_num == 1:
                defense = await self.advocate.present(analysis)
            else:
                defense = await self.advocate.respond(
                    analysis,
                    transcript[-1].challenges
                )
            
            # Challenger critiques
            challenges = await self.challenger.challenge(
                analysis,
                defense,
                previous_rounds=transcript
            )
            
            # Advocate responds to challenges
            responses = await self.advocate.rebut(challenges)
            
            transcript.append(DebateRound(
                round_number=round_num,
                advocate_defense=defense,
                challenges=challenges,
                responses=responses
            ))
        
        # Judge renders verdict
        judgment = await self.judge.adjudicate(analysis, transcript)
        
        return DebateResult(
            transcript=transcript,
            judgment=judgment,
            modifications=judgment.modifications,
            confidence_adjustment=judgment.confidence_adjustment
        )
```

---

## Phase 3: Production (Weeks 10-12)

### Week 10: Pass 4 & Article Generation

**Deliverables:**
- [ ] Article writer agent
- [ ] Voice calibration agent
- [ ] Self-critique agent
- [ ] Revision loop (2 cycles)
- [ ] Quality evaluation agent
- [ ] Pass 4 orchestrator
- [ ] Article assembly

**Code Focus:**

```python
# src/undertow/core/pipeline/pass4.py
class Pass4Orchestrator:
    """Orchestrates Pass 4: Production with critique-revision cycles."""
    
    MAX_REVISION_CYCLES = 2
    
    def __init__(self, router: ModelRouter):
        self.writer = ArticleWriterAgent(router)
        self.voice = VoiceCalibrationAgent(router)
        self.critic = SelfCritiqueAgent(router)
        self.evaluator = QualityEvaluationAgent(router)
        self.quality_gate = QualityGate("output", threshold=0.85)
    
    async def run(self, story: Story, all_analysis: dict) -> Pass4Output:
        # Initial draft
        article_draft = await self.writer.write(all_analysis)
        
        # Critique-revision cycles
        for cycle in range(self.MAX_REVISION_CYCLES):
            # Voice calibration
            voice_issues = await self.voice.check(article_draft)
            
            # Self-critique
            critique = await self.critic.critique(article_draft, all_analysis)
            
            if not voice_issues and critique.overall_score >= 0.90:
                break  # Good enough, skip revision
            
            # Revise based on feedback
            article_draft = await self.writer.revise(
                article_draft,
                voice_issues=voice_issues,
                critique=critique
            )
        
        # Final quality evaluation
        quality = await self.evaluator.evaluate(article_draft)
        
        if quality.weighted_score < self.quality_gate.threshold:
            # Flag for human review
            await self._escalate_for_review(story, article_draft, quality)
        
        return Pass4Output(
            article=article_draft,
            quality_score=quality.weighted_score,
            quality_details=quality
        )
```

### Week 11: Newsletter Assembly & Delivery

**Deliverables:**
- [ ] Preamble writer agent
- [ ] Newsletter assembler
- [ ] Edition model & service
- [ ] Email template (MJML)
- [ ] SendGrid integration
- [ ] Scheduling system
- [ ] Archive storage

### Week 12: Quality Gates & Human Review

**Deliverables:**
- [ ] Human review queue
- [ ] Escalation triggers
- [ ] Review assignment
- [ ] Review resolution flow
- [ ] Notification system (Slack, email)
- [ ] Review dashboard endpoints

---

## Phase 4: Polish (Weeks 13-16)

### Week 13: Admin Dashboard

**Deliverables:**
- [ ] Next.js admin app setup
- [ ] Source management UI
- [ ] Pipeline monitoring UI
- [ ] Story selection interface
- [ ] Human review interface
- [ ] Cost dashboard
- [ ] User management

### Week 14: Monitoring & Alerting

**Deliverables:**
- [ ] Prometheus metrics
- [ ] Grafana dashboards
- [ ] Alert rules
- [ ] Structured logging
- [ ] Error tracking (Sentry)
- [ ] Performance profiling

### Week 15: Testing & Bug Fixes

**Deliverables:**
- [ ] Unit test coverage (>80%)
- [ ] Integration tests
- [ ] E2E test suite
- [ ] Load testing
- [ ] Bug fixes
- [ ] Performance optimization

### Week 16: Deployment & Launch Prep

**Deliverables:**
- [ ] Production infrastructure (AWS/Railway)
- [ ] CI/CD for prod
- [ ] Database backups
- [ ] Runbooks
- [ ] Seed production sources
- [ ] Soft launch with limited audience

---

# SECTION 3: SPRINT BREAKDOWN

## Sprint 1 (Week 1-2): Foundation

| Task | Points | Owner |
|------|--------|-------|
| Project setup (Poetry, Docker, CI) | 3 | Backend |
| PostgreSQL + Redis infrastructure | 2 | Backend |
| FastAPI app skeleton | 2 | Backend |
| SQLAlchemy models (all entities) | 5 | Backend |
| Alembic migrations | 2 | Backend |
| Pydantic schemas | 3 | Backend |
| Source CRUD endpoints | 3 | Backend |
| JWT authentication | 3 | Backend |
| Basic tests setup | 2 | Backend |
| **Total** | **25** | |

## Sprint 2 (Week 3-4): Ingestion

| Task | Points | Owner |
|------|--------|-------|
| RSS fetcher | 3 | Backend |
| Web scraper | 5 | Backend |
| Article extractor (Trafilatura) | 3 | Backend |
| Language detection | 1 | Backend |
| Zone classifier | 3 | Backend |
| Entity extraction (spaCy) | 3 | Backend |
| Embedding generation | 3 | Backend |
| Celery task setup | 2 | Backend |
| Ingestion tasks | 3 | Backend |
| Source health monitoring | 2 | Backend |
| **Total** | **28** | |

## Sprint 3 (Week 5-6): LLM & Agents

| Task | Points | Owner |
|------|--------|-------|
| LLM provider abstraction | 5 | Backend |
| OpenAI provider | 3 | Backend |
| Anthropic provider | 3 | Backend |
| Model router | 5 | Backend |
| Cost tracker | 3 | Backend |
| Response cache | 3 | Backend |
| Base agent class | 3 | Backend |
| Prompt template system | 2 | Backend |
| Agent output validation | 2 | Backend |
| **Total** | **29** | |

## Sprint 4 (Week 7-8): Pass 1 & 2

| Task | Points | Owner |
|------|--------|-------|
| Story candidate generator | 3 | Backend |
| Story scorer agent | 3 | Backend |
| Factual reconstruction agent | 5 | Backend |
| Context analysis agent | 5 | Backend |
| Actor analysis agent | 3 | Backend |
| Motivation analysis agent | 8 | Backend |
| Chain mapping agent | 8 | Backend |
| Subtlety agent | 5 | Backend |
| Pass 1 orchestrator | 3 | Backend |
| Pass 2 orchestrator | 3 | Backend |
| **Total** | **46** | |

## Sprint 5 (Week 9): Adversarial

| Task | Points | Owner |
|------|--------|-------|
| Advocate agent | 5 | Backend |
| Challenger agent | 5 | Backend |
| Judge agent | 5 | Backend |
| Debate orchestrator | 5 | Backend |
| Fact checker agent | 5 | Backend |
| Source verifier | 5 | Backend |
| Pass 3 orchestrator | 3 | Backend |
| **Total** | **33** | |

## Sprint 6 (Week 10): Production

| Task | Points | Owner |
|------|--------|-------|
| Article writer agent | 8 | Backend |
| Voice calibration agent | 5 | Backend |
| Self-critique agent | 5 | Backend |
| Quality evaluation agent | 5 | Backend |
| Pass 4 orchestrator | 5 | Backend |
| Critique-revision loop | 3 | Backend |
| **Total** | **31** | |

## Sprint 7 (Week 11): Newsletter

| Task | Points | Owner |
|------|--------|-------|
| Preamble writer agent | 5 | Backend |
| Newsletter assembler | 5 | Backend |
| Edition service | 3 | Backend |
| MJML email template | 5 | Frontend |
| SendGrid integration | 3 | Backend |
| Scheduler (Celery Beat) | 3 | Backend |
| Archive storage (S3) | 2 | Backend |
| **Total** | **26** | |

## Sprint 8 (Week 12): Review System

| Task | Points | Owner |
|------|--------|-------|
| Human review queue | 3 | Backend |
| Escalation triggers | 3 | Backend |
| Review assignment logic | 3 | Backend |
| Review resolution flow | 3 | Backend |
| Slack notifications | 3 | Backend |
| Email notifications | 2 | Backend |
| Review endpoints | 3 | Backend |
| **Total** | **20** | |

## Sprint 9 (Week 13): Admin Dashboard

| Task | Points | Owner |
|------|--------|-------|
| Next.js setup | 3 | Frontend |
| Auth integration | 3 | Frontend |
| Source management UI | 5 | Frontend |
| Pipeline monitoring | 5 | Frontend |
| Story selection UI | 5 | Frontend |
| Review interface | 5 | Frontend |
| Cost dashboard | 3 | Frontend |
| **Total** | **29** | |

## Sprint 10 (Week 14): Monitoring

| Task | Points | Owner |
|------|--------|-------|
| Prometheus metrics | 5 | Backend |
| Grafana dashboards | 5 | Backend |
| Alert rules | 3 | Backend |
| Structured logging | 3 | Backend |
| Sentry integration | 2 | Backend |
| Performance profiling | 3 | Backend |
| **Total** | **21** | |

## Sprint 11 (Week 15): Testing

| Task | Points | Owner |
|------|--------|-------|
| Unit tests (agents) | 8 | Backend |
| Unit tests (services) | 5 | Backend |
| Integration tests | 8 | Backend |
| E2E tests | 5 | Backend |
| Load testing | 3 | Backend |
| Bug fixes | 8 | Both |
| **Total** | **37** | |

## Sprint 12 (Week 16): Launch

| Task | Points | Owner |
|------|--------|-------|
| Production infrastructure | 5 | DevOps |
| CI/CD for prod | 3 | DevOps |
| Database backups | 2 | DevOps |
| Runbooks | 3 | Both |
| Seed sources | 3 | Backend |
| Soft launch | 2 | Both |
| Monitoring verification | 2 | Both |
| **Total** | **20** | |

---

# SECTION 4: RISK MITIGATION

## Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| LLM API rate limits | Medium | High | Multiple providers, request queuing, exponential backoff |
| Cost overruns | Medium | Medium | Hard daily limits, tier routing, caching |
| Quality inconsistency | Medium | High | 4-gate system, adversarial review, human escalation |
| Latency issues | Medium | Medium | Async processing, Celery workers, caching |
| Source availability | Low | Medium | Health monitoring, fallback sources, manual addition |

## Mitigation Strategies

```python
# Example: Cost control circuit breaker
class BudgetController:
    def __init__(self, daily_limit: float):
        self.daily_limit = daily_limit
        self.redis = Redis()
        
    async def check_and_reserve(self, estimated_cost: float) -> bool:
        key = f"budget:{date.today()}"
        current = float(self.redis.get(key) or 0)
        
        if current + estimated_cost > self.daily_limit:
            await self._alert_budget_exceeded()
            return False
            
        self.redis.incrbyfloat(key, estimated_cost)
        return True
    
    async def _alert_budget_exceeded(self):
        # Send Slack alert
        # Pause non-critical tasks
        # Notify on-call
        pass
```

---

# SECTION 5: TEAM STRUCTURE

## Recommended Team (Minimal Viable)

| Role | Count | Responsibilities |
|------|-------|------------------|
| **Tech Lead / Architect** | 1 | Architecture, code review, complex features |
| **Backend Developer** | 2 | Python services, agents, pipeline |
| **Frontend Developer** | 1 | Admin dashboard, email templates |
| **DevOps** | 0.5 | Infrastructure, CI/CD (can be part-time) |

**Total: 4-5 people for 16 weeks**

## Solo Developer Path

If building alone, extend timeline to **24-32 weeks** with priorities:

1. **Weeks 1-4**: Foundation + Ingestion (critical path)
2. **Weeks 5-10**: Core agents (Pass 1-2)
3. **Weeks 11-14**: Production pipeline (Pass 3-4)
4. **Weeks 15-20**: Newsletter + basic admin
5. **Weeks 21-24**: Quality systems + monitoring
6. **Weeks 25-32**: Polish, testing, launch

---

# SECTION 6: GETTING STARTED

## Day 1 Checklist

```bash
# 1. Create project
mkdir undertow && cd undertow
git init

# 2. Setup Python environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install poetry
poetry init

# 3. Install core dependencies
poetry add fastapi uvicorn sqlalchemy asyncpg redis celery
poetry add openai anthropic langchain
poetry add pydantic pydantic-settings
poetry add --group dev pytest pytest-asyncio ruff mypy

# 4. Create structure
mkdir -p src/undertow/{api,core,agents,llm,models,schemas,services,tasks}
mkdir -p tests/{unit,integration}
mkdir -p prompts/{collection,analysis,adversarial,production}

# 5. Docker setup
touch docker-compose.yml Dockerfile .env.example

# 6. Start coding!
code .
```

## First API Endpoint

```python
# src/undertow/main.py
from fastapi import FastAPI
from src.undertow.config import get_settings

app = FastAPI(title="The Undertow API", version="1.0.0")

@app.get("/health")
async def health():
    return {"status": "healthy", "env": get_settings().app_env}

@app.get("/")
async def root():
    return {"message": "Welcome to The Undertow API"}
```

```bash
# Run it
uvicorn src.undertow.main:app --reload
```

---

# SECTION 7: KEY DECISION POINTS

## Decision 1: LangChain vs. Custom

**Recommendation: Hybrid**
- Use LangChain for prompt templates, output parsing
- Use custom orchestration for pipeline control
- Avoid LangChain agents (too opaque)

## Decision 2: pgvector vs. Pinecone

**Recommendation: Start with pgvector**
- Lower cost, simpler infrastructure
- Migrate to Pinecone if scale requires

## Decision 3: Celery vs. Background Tasks

**Recommendation: Celery**
- Long-running AI tasks need dedicated workers
- Better retry/failure handling
- Monitoring with Flower

## Decision 4: Monolith vs. Microservices

**Recommendation: Monolith first**
- Faster development
- Easier debugging
- Split later if needed

---

*This plan provides a clear path from zero to production. Adjust timelines based on team size and experience.*

