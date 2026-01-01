# The Undertow — Zero-Tolerance Coding Standards

## Absolute Engineering Excellence Requirements

---

# ⚠️ ZERO TOLERANCE POLICY

**This document defines NON-NEGOTIABLE coding standards. Violations will:**
1. **Block all PRs** — No exceptions, no "we'll fix it later"
2. **Trigger immediate refactoring** — Technical debt is not accepted
3. **Require explanation** — Violating developer must justify to team lead

**Our code is:**
- **Production-grade from day one** — Not "prototype that became production"
- **Maintainable by strangers** — Code is written for the next developer
- **Defensively engineered** — Assumes everything can fail
- **Explicitly typed** — No runtime surprises
- **Thoroughly tested** — Tests are first-class citizens

---

# TABLE OF CONTENTS

1. [Foundational Principles](#part-i-foundational-principles)
2. [Architecture Standards](#part-ii-architecture-standards)
3. [Multi-Agent Standards](#part-iii-multi-agent-standards)
4. [Type System Standards](#part-iv-type-system-standards)
5. [Error Handling Standards](#part-v-error-handling-standards)
6. [Testing Standards](#part-vi-testing-standards)
7. [Code Organization](#part-vii-code-organization)
8. [Naming & Style](#part-viii-naming--style)
9. [Documentation Standards](#part-ix-documentation-standards)
10. [Forbidden Patterns](#part-x-forbidden-patterns)
11. [Required Patterns](#part-xi-required-patterns)
12. [Review Enforcement](#part-xii-review-enforcement)

---

# PART I: FOUNDATIONAL PRINCIPLES

## 1.1 The Five Absolutes

### ABSOLUTE 1: Explicit Over Implicit

```python
# ❌ FORBIDDEN: Implicit behavior
def process(data):
    return handler(data)

# ✅ REQUIRED: Explicit in every dimension
async def process_article(
    article: Article,
    config: ProcessingConfig,
    *,  # Force keyword arguments for clarity
    validate: bool = True,
    timeout_seconds: float = 30.0
) -> ProcessingResult:
    """
    Process article with explicit configuration.
    
    Args:
        article: Article to process (required)
        config: Processing configuration (required)
        validate: Whether to validate output (default: True)
        timeout_seconds: Maximum processing time (default: 30.0)
        
    Returns:
        ProcessingResult with analysis and metadata
        
    Raises:
        ValidationError: If validate=True and output invalid
        TimeoutError: If processing exceeds timeout_seconds
    """
    ...
```

### ABSOLUTE 2: Fail Fast, Fail Loud

```python
# ❌ FORBIDDEN: Silent failures
def get_config(key):
    return config.get(key)  # Returns None silently

# ❌ FORBIDDEN: Swallowing exceptions
try:
    result = risky_operation()
except Exception:
    pass  # Silent failure

# ✅ REQUIRED: Immediate, loud failure
def get_config(key: str) -> ConfigValue:
    """Get configuration value. Raises if not found."""
    if key not in config:
        raise ConfigurationError(
            f"Required configuration '{key}' not found. "
            f"Available keys: {list(config.keys())}"
        )
    return config[key]

# ✅ REQUIRED: Explicit error handling
try:
    result = risky_operation()
except SpecificError as e:
    logger.error("Operation failed", error=str(e), context=context)
    raise OperationFailedError(f"Could not complete: {e}") from e
```

### ABSOLUTE 3: Single Responsibility

```python
# ❌ FORBIDDEN: God classes/functions
class ArticleProcessor:
    def process(self, article):
        # Fetches, parses, analyzes, writes, emails... 500 lines
        ...

# ✅ REQUIRED: Single, clear responsibility
class ArticleFetcher:
    """Fetches articles from sources. That's it."""
    
    async def fetch(self, url: str) -> RawArticle:
        ...

class ArticleParser:
    """Parses raw articles into structured data. That's it."""
    
    def parse(self, raw: RawArticle) -> ParsedArticle:
        ...

class ArticleAnalyzer:
    """Analyzes parsed articles. That's it."""
    
    async def analyze(self, article: ParsedArticle) -> Analysis:
        ...
```

### ABSOLUTE 4: Composition Over Inheritance

```python
# ❌ FORBIDDEN: Deep inheritance hierarchies
class BaseAgent:
    ...

class AnalysisAgent(BaseAgent):
    ...

class MotivationAnalysisAgent(AnalysisAgent):
    ...

class DetailedMotivationAnalysisAgent(MotivationAnalysisAgent):
    ...  # 4 levels deep = unmaintainable

# ✅ REQUIRED: Shallow inheritance + composition
class BaseAgent(ABC):
    """Abstract base with minimal shared behavior."""
    
    def __init__(
        self,
        router: ModelRouter,
        validator: OutputValidator,
        metrics: MetricsCollector
    ):
        self.router = router
        self.validator = validator
        self.metrics = metrics

class MotivationAnalysisAgent(BaseAgent):
    """Concrete agent using composition for specialized behavior."""
    
    def __init__(
        self,
        router: ModelRouter,
        validator: OutputValidator,
        metrics: MetricsCollector,
        # Composed behaviors
        critique_strategy: CritiqueStrategy,
        output_formatter: MotivationFormatter
    ):
        super().__init__(router, validator, metrics)
        self.critique = critique_strategy
        self.formatter = output_formatter
```

### ABSOLUTE 5: Immutability by Default

```python
# ❌ FORBIDDEN: Mutable shared state
class Config:
    settings = {}  # Mutable class variable = bugs
    
    def update(self, key, value):
        self.settings[key] = value  # Global mutation

# ✅ REQUIRED: Immutable data structures
from dataclasses import dataclass
from typing import FrozenSet

@dataclass(frozen=True)  # Immutable
class AnalysisConfig:
    """Immutable configuration."""
    
    quality_threshold: float
    max_retries: int
    enabled_agents: FrozenSet[str]
    
    def with_threshold(self, new_threshold: float) -> "AnalysisConfig":
        """Return new config with updated threshold."""
        return AnalysisConfig(
            quality_threshold=new_threshold,
            max_retries=self.max_retries,
            enabled_agents=self.enabled_agents
        )
```

## 1.2 The Quality Bar

| Metric | Minimum | Target | Measured By |
|--------|---------|--------|-------------|
| **Type Coverage** | 100% | 100% | mypy --strict |
| **Test Coverage** | 85% | 95% | pytest-cov |
| **Cyclomatic Complexity** | ≤10 | ≤7 | radon |
| **Function Length** | ≤50 lines | ≤30 lines | pylint |
| **Class Length** | ≤300 lines | ≤200 lines | pylint |
| **Import Depth** | ≤4 levels | ≤3 levels | import-linter |
| **Documentation** | 100% public | 100% all | interrogate |

---

# PART II: ARCHITECTURE STANDARDS

## 2.1 Layer Architecture (MANDATORY)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MANDATORY LAYER ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  PRESENTATION LAYER (api/)                                          │   │
│  │  • HTTP request/response handling ONLY                              │   │
│  │  • Input validation via Pydantic                                    │   │
│  │  • Output serialization                                             │   │
│  │  • NO business logic                                                │   │
│  │  • NO database access                                               │   │
│  │  • NO LLM calls                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │ calls                                        │
│                              ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  APPLICATION LAYER (services/)                                      │   │
│  │  • Orchestrates use cases                                           │   │
│  │  • Transaction boundaries                                           │   │
│  │  • Business rule enforcement                                        │   │
│  │  • Coordinates domain objects                                       │   │
│  │  • NO HTTP concerns                                                 │   │
│  │  • NO direct LLM calls (delegates to agents)                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │ calls                                        │
│                              ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  DOMAIN LAYER (core/, agents/)                                      │   │
│  │  • Business logic                                                   │   │
│  │  • Domain models                                                    │   │
│  │  • Agent implementations                                            │   │
│  │  • NO infrastructure concerns                                       │   │
│  │  • NO database queries                                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │ uses                                         │
│                              ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  INFRASTRUCTURE LAYER (models/, llm/, external/)                    │   │
│  │  • Database implementations                                         │   │
│  │  • LLM provider clients                                             │   │
│  │  • External service integrations                                    │   │
│  │  • Caching implementations                                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

DEPENDENCY RULE: Dependencies point INWARD only.
                 Outer layers depend on inner layers.
                 Inner layers NEVER depend on outer layers.
```

## 2.2 Import Rules (ENFORCED BY CI)

```python
# pyproject.toml - import-linter configuration

[tool.importlinter]
root_package = "undertow"
include_external_packages = true

[[tool.importlinter.contracts]]
name = "Layer dependencies"
type = "layers"
layers = [
    "undertow.api",
    "undertow.services", 
    "undertow.core",
    "undertow.agents",
    "undertow.infrastructure",
]
containers = ["undertow"]

[[tool.importlinter.contracts]]
name = "Agents cannot import services"
type = "forbidden"
source_modules = ["undertow.agents"]
forbidden_modules = ["undertow.services", "undertow.api"]

[[tool.importlinter.contracts]]
name = "Core cannot import infrastructure"
type = "forbidden"
source_modules = ["undertow.core"]
forbidden_modules = ["undertow.infrastructure", "undertow.api"]

[[tool.importlinter.contracts]]
name = "No circular imports"
type = "independence"
modules = [
    "undertow.api",
    "undertow.services",
    "undertow.core",
    "undertow.agents",
]
```

## 2.3 Module Boundaries

```python
# EACH MODULE HAS A SINGLE PUBLIC INTERFACE

# ❌ FORBIDDEN: Importing internals
from undertow.agents.analysis.motivation.helpers import extract_actors
from undertow.services.article_service import _internal_validate

# ✅ REQUIRED: Import from module's public interface
from undertow.agents import MotivationAnalysisAgent
from undertow.services import ArticleService

# MODULE STRUCTURE:
# undertow/agents/
# ├── __init__.py          # PUBLIC INTERFACE - exports only public classes
# ├── base.py              # Internal
# └── analysis/
#     ├── __init__.py      # Exports analysis agents
#     ├── motivation.py    # Internal implementation
#     └── helpers.py       # Internal helpers - NOT exported

# agents/__init__.py
"""
Public interface for agents module.

Only classes/functions listed here are part of the public API.
"""
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

__all__ = [
    "MotivationAnalysisAgent",
    "ChainMappingAgent", 
    "SubtletyAnalysisAgent",
    "AdvocateAgent",
    "ChallengerAgent",
    "JudgeAgent",
]
```

---

# PART III: MULTI-AGENT STANDARDS

## 3.1 Agent Contract (MANDATORY)

Every agent MUST implement this exact contract:

```python
# src/undertow/agents/base.py

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, ClassVar
from pydantic import BaseModel
from datetime import datetime

InputT = TypeVar("InputT", bound=BaseModel)
OutputT = TypeVar("OutputT", bound=BaseModel)

class AgentMetadata(BaseModel):
    """Metadata returned with every agent execution."""
    
    agent_name: str
    agent_version: str
    execution_id: str
    started_at: datetime
    completed_at: datetime
    duration_ms: int
    model_used: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    quality_score: float | None
    retries: int
    cache_hit: bool

class AgentResult(BaseModel, Generic[OutputT]):
    """Standardized result wrapper for all agents."""
    
    success: bool
    output: OutputT | None
    error: str | None
    metadata: AgentMetadata

class BaseAgent(ABC, Generic[InputT, OutputT]):
    """
    Abstract base class for all agents.
    
    EVERY agent MUST:
    1. Inherit from this class
    2. Define task_name, version, input_schema, output_schema
    3. Implement _build_messages() and _parse_output()
    4. Return AgentResult (not raw output)
    """
    
    # REQUIRED: Class variables that MUST be defined
    task_name: ClassVar[str]
    version: ClassVar[str]
    input_schema: ClassVar[type[InputT]]
    output_schema: ClassVar[type[OutputT]]
    
    # REQUIRED: Model tier for this agent
    default_tier: ClassVar[ModelTier] = ModelTier.STANDARD
    
    def __init__(
        self,
        router: ModelRouter,
        validator: OutputValidator,
        metrics: MetricsCollector,
        config: AgentConfig | None = None
    ):
        self.router = router
        self.validator = validator
        self.metrics = metrics
        self.config = config or AgentConfig()
        
        # Validate class is properly configured
        self._validate_agent_configuration()
    
    def _validate_agent_configuration(self) -> None:
        """Validate agent is properly configured. Called on init."""
        required = ["task_name", "version", "input_schema", "output_schema"]
        for attr in required:
            if not hasattr(self, attr) or getattr(self, attr) is None:
                raise AgentConfigurationError(
                    f"Agent {self.__class__.__name__} missing required "
                    f"class variable: {attr}"
                )
    
    async def run(self, input: InputT) -> AgentResult[OutputT]:
        """
        Execute the agent.
        
        This is the ONLY public method for agent execution.
        Do not call internal methods directly.
        """
        execution_id = str(uuid4())
        started_at = datetime.utcnow()
        retries = 0
        cache_hit = False
        
        try:
            # Check cache
            cache_key = self._build_cache_key(input)
            cached = await self._check_cache(cache_key)
            if cached:
                cache_hit = True
                output = cached
            else:
                # Execute with retries
                output, retries = await self._execute_with_retries(input)
                await self._store_cache(cache_key, output)
            
            # Validate output
            validated = self.validator.validate(
                output, 
                self.output_schema,
                self.task_name
            )
            
            # Calculate quality
            quality_score = await self._assess_quality(validated, input)
            
            completed_at = datetime.utcnow()
            
            return AgentResult(
                success=True,
                output=validated,
                error=None,
                metadata=AgentMetadata(
                    agent_name=self.task_name,
                    agent_version=self.version,
                    execution_id=execution_id,
                    started_at=started_at,
                    completed_at=completed_at,
                    duration_ms=int((completed_at - started_at).total_seconds() * 1000),
                    model_used=self.router.last_model_used,
                    input_tokens=self.router.last_input_tokens,
                    output_tokens=self.router.last_output_tokens,
                    cost_usd=self.router.last_cost,
                    quality_score=quality_score,
                    retries=retries,
                    cache_hit=cache_hit
                )
            )
            
        except Exception as e:
            completed_at = datetime.utcnow()
            logger.error(
                "Agent execution failed",
                agent=self.task_name,
                error=str(e),
                execution_id=execution_id
            )
            
            return AgentResult(
                success=False,
                output=None,
                error=str(e),
                metadata=AgentMetadata(
                    agent_name=self.task_name,
                    agent_version=self.version,
                    execution_id=execution_id,
                    started_at=started_at,
                    completed_at=completed_at,
                    duration_ms=int((completed_at - started_at).total_seconds() * 1000),
                    model_used="",
                    input_tokens=0,
                    output_tokens=0,
                    cost_usd=0.0,
                    quality_score=None,
                    retries=retries,
                    cache_hit=False
                )
            )
    
    @abstractmethod
    def _build_messages(self, input: InputT) -> list[dict[str, str]]:
        """
        Build LLM messages from input.
        
        MUST be implemented by all agents.
        """
        pass
    
    @abstractmethod
    def _parse_output(self, content: str) -> OutputT:
        """
        Parse LLM response into output schema.
        
        MUST be implemented by all agents.
        """
        pass
    
    @abstractmethod
    async def _assess_quality(
        self, 
        output: OutputT, 
        input: InputT
    ) -> float:
        """
        Assess output quality (0.0 to 1.0).
        
        MUST be implemented by all agents.
        """
        pass
```

## 3.2 Agent Implementation Requirements

```python
# COMPLETE AGENT IMPLEMENTATION EXAMPLE

from undertow.agents.base import BaseAgent, AgentResult
from undertow.schemas.agents import MotivationInput, MotivationOutput
from undertow.llm.router import ModelRouter, ModelTier

class MotivationAnalysisAgent(BaseAgent[MotivationInput, MotivationOutput]):
    """
    Four-layer motivation analysis agent.
    
    Analyzes motivations behind geopolitical events by examining:
    - Layer 1: Individual decision-maker
    - Layer 2: Institutional interests
    - Layer 3: Structural pressures
    - Layer 4: Opportunistic window
    
    Version History:
        1.0.0 - Initial implementation
        1.1.0 - Added alternative hypothesis generation
        1.2.0 - Improved confidence calibration
    
    Example:
        >>> agent = MotivationAnalysisAgent(router, validator, metrics)
        >>> result = await agent.run(MotivationInput(story=story, context=context))
        >>> if result.success:
        ...     print(result.output.synthesis.primary_driver)
    """
    
    # REQUIRED class variables
    task_name: ClassVar[str] = "motivation_analysis"
    version: ClassVar[str] = "1.2.0"
    input_schema: ClassVar[type] = MotivationInput
    output_schema: ClassVar[type] = MotivationOutput
    default_tier: ClassVar[ModelTier] = ModelTier.FRONTIER
    
    # Agent-specific configuration
    SYSTEM_PROMPT: ClassVar[str] = """You are a senior intelligence analyst..."""
    MIN_ALTERNATIVES: ClassVar[int] = 2
    
    def __init__(
        self,
        router: ModelRouter,
        validator: OutputValidator,
        metrics: MetricsCollector,
        config: AgentConfig | None = None,
        *,
        # Agent-specific dependencies (composed, not inherited)
        prompt_loader: PromptLoader,
    ):
        super().__init__(router, validator, metrics, config)
        self.prompt_loader = prompt_loader
    
    def _build_messages(self, input: MotivationInput) -> list[dict[str, str]]:
        """Build messages for motivation analysis."""
        
        system_prompt = self.prompt_loader.load(
            "analysis/motivation",
            version="latest"
        )
        
        user_content = self._format_user_prompt(input)
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
    
    def _format_user_prompt(self, input: MotivationInput) -> str:
        """Format user prompt with story and context."""
        
        return f"""
## Story to Analyze

**Headline:** {input.story.headline}
**Summary:** {input.story.summary}
**Key Events:**
{self._format_events(input.story.events)}

## Available Context

**Actors:**
{self._format_actors(input.context.actors)}

**Recent History:**
{self._format_history(input.context.history)}

## Your Task

Analyze the motivations behind this event using the four-layer framework.
Output valid JSON matching the required schema.
"""
    
    def _parse_output(self, content: str) -> MotivationOutput:
        """Parse and validate LLM output."""
        
        try:
            # Extract JSON from response
            json_str = self._extract_json(content)
            data = json.loads(json_str)
            
            # Validate with Pydantic
            return MotivationOutput.model_validate(data)
            
        except json.JSONDecodeError as e:
            raise OutputParseError(
                agent=self.task_name,
                error=f"Invalid JSON: {e}",
                raw_content=content
            )
        except ValidationError as e:
            raise OutputValidationError(
                agent=self.task_name,
                error=f"Schema validation failed: {e}",
                raw_content=content
            )
    
    async def _assess_quality(
        self, 
        output: MotivationOutput,
        input: MotivationInput
    ) -> float:
        """Assess output quality."""
        
        scores = []
        
        # Completeness: All 4 layers present and filled
        layer_score = self._score_layer_completeness(output)
        scores.append(("completeness", layer_score, 0.25))
        
        # Depth: Sufficient detail in each layer
        depth_score = self._score_depth(output)
        scores.append(("depth", depth_score, 0.25))
        
        # Alternatives: Required number with genuine alternatives
        alt_score = self._score_alternatives(output)
        scores.append(("alternatives", alt_score, 0.20))
        
        # Confidence calibration: Reasonable distribution
        conf_score = self._score_confidence_calibration(output)
        scores.append(("calibration", conf_score, 0.15))
        
        # Evidence grounding: Claims cite evidence
        evidence_score = self._score_evidence_grounding(output)
        scores.append(("evidence", evidence_score, 0.15))
        
        # Weighted average
        total = sum(score * weight for _, score, weight in scores)
        
        # Log detailed scores
        logger.debug(
            "Quality assessment",
            agent=self.task_name,
            scores={name: score for name, score, _ in scores},
            total=total
        )
        
        return total
    
    def _score_layer_completeness(self, output: MotivationOutput) -> float:
        """Score layer completeness (0-1)."""
        layers = [
            output.layer1_individual,
            output.layer2_institutional,
            output.layer3_structural,
            output.layer4_window
        ]
        
        filled = sum(1 for layer in layers if layer and len(layer.dict()) > 2)
        return filled / 4.0
```

## 3.3 Agent Communication Standards

```python
# Agents communicate through TYPED messages, never raw dicts

# ❌ FORBIDDEN: Untyped communication
result = agent1.run({"story": story, "stuff": data})
agent2.run({"input": result})

# ✅ REQUIRED: Typed message passing
from undertow.schemas.messages import (
    MotivationInput,
    MotivationOutput,
    ChainMappingInput
)

# Agent 1 execution
motivation_input = MotivationInput(
    story=story,
    context=context,
    config=config
)
motivation_result = await motivation_agent.run(motivation_input)

if not motivation_result.success:
    raise AgentExecutionError(motivation_result.error)

# Agent 2 receives typed output
chain_input = ChainMappingInput(
    story=story,
    motivation_analysis=motivation_result.output,  # Typed!
    context=context
)
chain_result = await chain_agent.run(chain_input)
```

## 3.4 Agent Orchestration Patterns

```python
# src/undertow/core/orchestration.py

class AgentOrchestrator:
    """
    Orchestrates agent execution with proper patterns.
    
    Patterns:
    1. Sequential with dependency
    2. Parallel with aggregation
    3. Conditional execution
    4. Retry with fallback
    """
    
    async def execute_sequential(
        self,
        agents: list[tuple[BaseAgent, Callable[[dict], BaseModel]]],
        initial_input: BaseModel,
        context: dict
    ) -> list[AgentResult]:
        """
        Execute agents sequentially, passing outputs forward.
        
        Args:
            agents: List of (agent, input_builder) tuples
            initial_input: Input for first agent
            context: Shared context updated after each agent
        """
        results = []
        current_input = initial_input
        
        for agent, input_builder in agents:
            result = await agent.run(current_input)
            results.append(result)
            
            if not result.success:
                logger.error(
                    "Sequential execution failed",
                    failed_agent=agent.task_name,
                    error=result.error
                )
                break
            
            # Update context with output
            context[agent.task_name] = result.output
            
            # Build input for next agent
            if input_builder:
                current_input = input_builder(context)
        
        return results
    
    async def execute_parallel(
        self,
        agents: list[BaseAgent],
        inputs: list[BaseModel],
        *,
        max_concurrent: int = 5,
        fail_fast: bool = False
    ) -> list[AgentResult]:
        """
        Execute agents in parallel with concurrency control.
        
        Args:
            agents: Agents to execute
            inputs: Corresponding inputs
            max_concurrent: Maximum concurrent executions
            fail_fast: Stop all on first failure
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def run_with_semaphore(
            agent: BaseAgent, 
            input: BaseModel
        ) -> AgentResult:
            async with semaphore:
                return await agent.run(input)
        
        if fail_fast:
            # Use gather with return_exceptions=False
            results = await asyncio.gather(
                *(run_with_semaphore(a, i) for a, i in zip(agents, inputs))
            )
        else:
            # Collect all results even if some fail
            tasks = [
                run_with_semaphore(a, i) 
                for a, i in zip(agents, inputs)
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Convert exceptions to failed results
            results = [
                r if isinstance(r, AgentResult)
                else AgentResult(success=False, output=None, error=str(r), metadata=None)
                for r in results
            ]
        
        return results
    
    async def execute_with_fallback(
        self,
        primary: BaseAgent,
        fallback: BaseAgent,
        input: BaseModel,
        *,
        primary_timeout: float = 60.0
    ) -> AgentResult:
        """
        Execute primary agent with fallback on failure.
        """
        try:
            result = await asyncio.wait_for(
                primary.run(input),
                timeout=primary_timeout
            )
            if result.success:
                return result
        except asyncio.TimeoutError:
            logger.warning(
                "Primary agent timed out, using fallback",
                primary=primary.task_name,
                fallback=fallback.task_name
            )
        except Exception as e:
            logger.warning(
                "Primary agent failed, using fallback",
                primary=primary.task_name,
                fallback=fallback.task_name,
                error=str(e)
            )
        
        # Execute fallback
        return await fallback.run(input)
```

---

# PART IV: TYPE SYSTEM STANDARDS

## 4.1 Type Annotation Requirements

```python
# EVERY function, method, variable MUST be typed

# ❌ FORBIDDEN: Missing ANY type annotation
def process(data):
    result = transform(data)
    return result

class Service:
    def __init__(self, db):
        self.db = db

# ✅ REQUIRED: Complete type annotations
from typing import TypeVar, Generic, Callable, Awaitable

T = TypeVar("T")
R = TypeVar("R")

async def process(data: InputData) -> ProcessResult:
    result: TransformResult = await transform(data)
    return ProcessResult(data=result)

class Service:
    def __init__(self, db: AsyncSession) -> None:
        self.db: AsyncSession = db
```

## 4.2 Pydantic Model Standards

```python
# ALL data structures MUST be Pydantic models

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Literal
from datetime import datetime

class StrictBaseModel(BaseModel):
    """
    Base model with strict validation.
    
    ALL schemas MUST inherit from this.
    """
    
    model_config = {
        # Forbid extra fields
        "extra": "forbid",
        
        # Validate on assignment
        "validate_assignment": True,
        
        # Use enum values in serialization
        "use_enum_values": True,
        
        # Validate default values
        "validate_default": True,
        
        # Strict mode - no coercion
        "strict": True,
    }

class MotivationLayerAssessment(StrictBaseModel):
    """Assessment of a single motivation layer element."""
    
    finding: str = Field(
        ...,
        min_length=50,
        max_length=2000,
        description="Detailed finding for this element"
    )
    evidence: list[str] = Field(
        ...,
        min_length=1,
        description="Evidence supporting the finding"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence level (0-1)"
    )
    
    @field_validator("confidence")
    @classmethod
    def validate_confidence_granularity(cls, v: float) -> float:
        """Confidence should be in 0.05 increments."""
        return round(v * 20) / 20  # Round to nearest 0.05

class MotivationOutput(StrictBaseModel):
    """Complete motivation analysis output."""
    
    layer1_individual: MotivationLayer1
    layer2_institutional: MotivationLayer2
    layer3_structural: MotivationLayer3
    layer4_window: MotivationLayer4
    synthesis: MotivationSynthesis
    
    @model_validator(mode="after")
    def validate_synthesis_consistency(self) -> "MotivationOutput":
        """Ensure synthesis references valid layers."""
        valid_drivers = {
            "layer1_individual",
            "layer2_institutional", 
            "layer3_structural",
            "layer4_window"
        }
        if self.synthesis.primary_driver not in valid_drivers:
            raise ValueError(
                f"primary_driver must be one of {valid_drivers}"
            )
        return self
```

## 4.3 Generic Types and Protocols

```python
# Use Generics and Protocols for flexibility with type safety

from typing import Protocol, TypeVar, Generic, runtime_checkable

T = TypeVar("T")
InputT = TypeVar("InputT", bound=BaseModel)
OutputT = TypeVar("OutputT", bound=BaseModel)

@runtime_checkable
class Runnable(Protocol[InputT, OutputT]):
    """Protocol for anything that can be run."""
    
    async def run(self, input: InputT) -> OutputT:
        """Execute with typed input and output."""
        ...

@runtime_checkable
class Cacheable(Protocol):
    """Protocol for cacheable objects."""
    
    def cache_key(self) -> str:
        """Return cache key for this object."""
        ...
    
    def cache_ttl(self) -> int:
        """Return cache TTL in seconds."""
        ...

class Repository(Generic[T]):
    """Generic repository with type safety."""
    
    def __init__(self, session: AsyncSession, model: type[T]):
        self.session = session
        self.model = model
    
    async def get(self, id: UUID) -> T | None:
        """Get entity by ID."""
        result = await self.session.get(self.model, id)
        return result
    
    async def create(self, entity: T) -> T:
        """Create new entity."""
        self.session.add(entity)
        await self.session.flush()
        return entity

# Usage with full type safety
article_repo: Repository[Article] = Repository(session, Article)
article: Article | None = await article_repo.get(article_id)
```

---

# PART V: ERROR HANDLING STANDARDS

## 5.1 Exception Hierarchy

```python
# src/undertow/exceptions.py

"""
Exception hierarchy for The Undertow.

ALL exceptions MUST inherit from UndertowError.
NO bare Exception raises allowed.
"""

class UndertowError(Exception):
    """Base exception for all Undertow errors."""
    
    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        details: dict | None = None
    ):
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}

# Domain Errors
class DomainError(UndertowError):
    """Errors in domain/business logic."""
    pass

class ValidationError(DomainError):
    """Input or output validation failed."""
    pass

class BusinessRuleViolation(DomainError):
    """Business rule was violated."""
    pass

# Infrastructure Errors
class InfrastructureError(UndertowError):
    """Errors in infrastructure layer."""
    pass

class DatabaseError(InfrastructureError):
    """Database operation failed."""
    pass

class ExternalServiceError(InfrastructureError):
    """External service call failed."""
    pass

class LLMError(ExternalServiceError):
    """LLM API call failed."""
    pass

class RateLimitError(LLMError):
    """Rate limit exceeded."""
    pass

# Agent Errors
class AgentError(UndertowError):
    """Errors in agent execution."""
    pass

class AgentConfigurationError(AgentError):
    """Agent is misconfigured."""
    pass

class AgentExecutionError(AgentError):
    """Agent execution failed."""
    pass

class OutputParseError(AgentError):
    """Could not parse agent output."""
    pass

class OutputValidationError(AgentError):
    """Agent output failed validation."""
    pass
```

## 5.2 Error Handling Patterns

```python
# MANDATORY error handling patterns

# ❌ FORBIDDEN: Catching bare Exception
try:
    result = await risky_operation()
except Exception:
    return None

# ❌ FORBIDDEN: Silent exception swallowing
try:
    result = await risky_operation()
except SomeError:
    pass

# ❌ FORBIDDEN: Raising bare Exception
if not valid:
    raise Exception("Invalid")

# ✅ REQUIRED: Specific exception handling with context
async def process_article(article: Article) -> ProcessResult:
    """Process article with proper error handling."""
    
    try:
        validated = await validate_article(article)
    except ValidationError as e:
        logger.warning(
            "Article validation failed",
            article_id=str(article.id),
            errors=e.details
        )
        raise ArticleValidationError(
            f"Article {article.id} failed validation: {e.message}",
            details={"article_id": str(article.id), "errors": e.details}
        ) from e
    
    try:
        analysis = await analyze_article(validated)
    except LLMError as e:
        logger.error(
            "LLM analysis failed",
            article_id=str(article.id),
            llm_error=str(e)
        )
        # Decide: retry, fallback, or propagate
        if isinstance(e, RateLimitError):
            # Retry with backoff
            await asyncio.sleep(e.retry_after)
            analysis = await analyze_article(validated)
        else:
            raise AnalysisError(
                f"Could not analyze article {article.id}",
                details={"article_id": str(article.id)}
            ) from e
    
    return ProcessResult(article=validated, analysis=analysis)
```

## 5.3 Result Type Pattern

```python
# For operations that can fail expectedly, use Result type

from typing import Generic, TypeVar
from dataclasses import dataclass

T = TypeVar("T")
E = TypeVar("E", bound=Exception)

@dataclass(frozen=True)
class Ok(Generic[T]):
    """Successful result."""
    value: T
    
    @property
    def is_ok(self) -> bool:
        return True
    
    @property
    def is_err(self) -> bool:
        return False

@dataclass(frozen=True)  
class Err(Generic[E]):
    """Error result."""
    error: E
    
    @property
    def is_ok(self) -> bool:
        return False
    
    @property
    def is_err(self) -> bool:
        return True

Result = Ok[T] | Err[E]

# Usage
async def fetch_article(url: str) -> Result[Article, FetchError]:
    """Fetch article, returning Result instead of raising."""
    
    try:
        response = await client.get(url, timeout=30.0)
        response.raise_for_status()
        return Ok(Article.from_response(response))
    except httpx.TimeoutException:
        return Err(FetchError.TIMEOUT)
    except httpx.HTTPStatusError as e:
        return Err(FetchError.HTTP_ERROR)

# Caller handles result explicitly
result = await fetch_article(url)
match result:
    case Ok(article):
        await process(article)
    case Err(FetchError.TIMEOUT):
        logger.warning("Fetch timed out", url=url)
        await schedule_retry(url)
    case Err(error):
        logger.error("Fetch failed", url=url, error=error)
```

---

# PART VI: TESTING STANDARDS

## 6.1 Test Requirements

```python
# MANDATORY test coverage and patterns

"""
TEST REQUIREMENTS:

1. Every public function MUST have tests
2. Every agent MUST have:
   - Unit tests for message building
   - Unit tests for output parsing
   - Integration tests with mocked LLM
   - Golden tests with expected outputs
3. Coverage MUST meet thresholds:
   - Core: 95%
   - Agents: 90%
   - Services: 90%
   - API: 85%
   - Overall: 85%
"""

# pyproject.toml
[tool.pytest.ini_options]
minversion = "7.0"
addopts = [
    "-ra",
    "--strict-markers",
    "--strict-config",
    "-v",
]
testpaths = ["tests"]
markers = [
    "unit: Unit tests (fast, isolated)",
    "integration: Integration tests",
    "e2e: End-to-end tests",
    "slow: Slow tests (>5s)",
    "llm: Tests requiring LLM calls",
]

[tool.coverage.run]
branch = true
source = ["src/undertow"]

[tool.coverage.report]
fail_under = 85
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
]
```

## 6.2 Test Organization

```
tests/
├── conftest.py              # Shared fixtures
├── factories.py             # Test data factories
│
├── unit/                    # Fast, isolated tests
│   ├── agents/
│   │   ├── test_motivation_agent.py
│   │   └── test_chain_agent.py
│   ├── core/
│   │   └── test_quality_gates.py
│   └── services/
│       └── test_article_service.py
│
├── integration/             # Tests with real(ish) dependencies
│   ├── test_pipeline.py
│   └── test_database.py
│
├── e2e/                     # Full system tests
│   └── test_full_pipeline.py
│
└── golden/                  # Expected output tests
    ├── motivation/
    │   ├── input_1.json
    │   └── expected_1.json
    └── chains/
        ├── input_1.json
        └── expected_1.json
```

## 6.3 Test Patterns

```python
# tests/conftest.py

import pytest
from unittest.mock import AsyncMock, MagicMock
from src.undertow.llm.router import ModelRouter

@pytest.fixture
def mock_router() -> ModelRouter:
    """
    Mock router for testing agents without LLM calls.
    
    ALL agent tests MUST use this fixture unless marked @pytest.mark.llm
    """
    router = MagicMock(spec=ModelRouter)
    router.complete = AsyncMock()
    return router

@pytest.fixture
def mock_llm_response():
    """Factory for mock LLM responses."""
    def _create(content: str, tokens: int = 100):
        return LLMResponse(
            content=content,
            input_tokens=tokens,
            output_tokens=tokens // 2,
            model="test-model",
            latency_ms=100,
            cost_usd=0.001
        )
    return _create

# tests/unit/agents/test_motivation_agent.py

import pytest
from src.undertow.agents.analysis import MotivationAnalysisAgent
from tests.factories import StoryFactory, ContextFactory

class TestMotivationAnalysisAgent:
    """Unit tests for MotivationAnalysisAgent."""
    
    @pytest.fixture
    def agent(self, mock_router, mock_validator, mock_metrics):
        """Create agent with mocked dependencies."""
        return MotivationAnalysisAgent(
            router=mock_router,
            validator=mock_validator,
            metrics=mock_metrics,
            prompt_loader=MockPromptLoader()
        )
    
    class TestMessageBuilding:
        """Tests for _build_messages method."""
        
        def test_includes_story_headline(self, agent):
            """Messages include story headline."""
            story = StoryFactory.create(headline="Test Headline")
            input = MotivationInput(story=story, context=ContextFactory.create())
            
            messages = agent._build_messages(input)
            
            user_message = messages[-1]["content"]
            assert "Test Headline" in user_message
        
        def test_includes_all_actors(self, agent):
            """Messages include all actor profiles."""
            actors = [ActorFactory.create(name=f"Actor {i}") for i in range(3)]
            context = ContextFactory.create(actors=actors)
            input = MotivationInput(story=StoryFactory.create(), context=context)
            
            messages = agent._build_messages(input)
            
            user_message = messages[-1]["content"]
            for actor in actors:
                assert actor.name in user_message
    
    class TestOutputParsing:
        """Tests for _parse_output method."""
        
        def test_parses_valid_json(self, agent):
            """Parses valid JSON output."""
            valid_output = json.dumps({
                "layer1_individual": {...},
                "layer2_institutional": {...},
                "layer3_structural": {...},
                "layer4_window": {...},
                "synthesis": {...}
            })
            
            result = agent._parse_output(valid_output)
            
            assert isinstance(result, MotivationOutput)
        
        def test_raises_on_invalid_json(self, agent):
            """Raises OutputParseError on invalid JSON."""
            with pytest.raises(OutputParseError):
                agent._parse_output("not json")
        
        def test_raises_on_missing_fields(self, agent):
            """Raises OutputValidationError on missing required fields."""
            incomplete = json.dumps({"layer1_individual": {}})
            
            with pytest.raises(OutputValidationError):
                agent._parse_output(incomplete)
    
    class TestQualityAssessment:
        """Tests for _assess_quality method."""
        
        @pytest.mark.parametrize("completeness,expected_min", [
            (4, 0.9),  # All layers complete
            (3, 0.7),  # 3 layers complete
            (2, 0.5),  # 2 layers complete
        ])
        async def test_quality_scales_with_completeness(
            self, 
            agent,
            completeness,
            expected_min
        ):
            """Quality score scales with layer completeness."""
            output = MotivationOutputFactory.create(
                complete_layers=completeness
            )
            input = MotivationInputFactory.create()
            
            score = await agent._assess_quality(output, input)
            
            assert score >= expected_min

# tests/golden/test_motivation_golden.py

import pytest
from pathlib import Path

GOLDEN_DIR = Path(__file__).parent / "motivation"

class TestMotivationGolden:
    """Golden tests comparing actual output to expected."""
    
    @pytest.mark.parametrize("case", [
        "somaliland_recognition",
        "ukraine_offensive",
        "sahel_coup",
    ])
    async def test_golden_case(self, agent, case):
        """Test against golden expected output."""
        input_path = GOLDEN_DIR / f"{case}_input.json"
        expected_path = GOLDEN_DIR / f"{case}_expected.json"
        
        input_data = MotivationInput.model_validate_json(input_path.read_text())
        expected = MotivationOutput.model_validate_json(expected_path.read_text())
        
        result = await agent.run(input_data)
        
        # Compare key fields (not exact match due to LLM variance)
        assert result.output.synthesis.primary_driver == expected.synthesis.primary_driver
        assert len(result.output.synthesis.alternatives) >= len(expected.synthesis.alternatives)
```

---

# PART VII: CODE ORGANIZATION

## 7.1 File Size Limits

```
HARD LIMITS (enforced by CI):

| Metric              | Hard Limit | Soft Limit |
|---------------------|------------|------------|
| Lines per file      | 500        | 300        |
| Lines per function  | 50         | 30         |
| Lines per class     | 300        | 200        |
| Parameters per func | 7          | 5          |
| Nesting depth       | 4          | 3          |
```

## 7.2 Function Structure

```python
# EVERY function follows this structure

async def analyze_motivation(
    story: Story,
    context: AnalysisContext,
    *,
    config: AnalysisConfig | None = None,
    timeout: float = 60.0
) -> MotivationResult:
    """
    [1] ONE-LINE SUMMARY
    Analyze motivations behind story events.
    
    [2] DETAILED DESCRIPTION (if needed)
    Performs four-layer motivation analysis examining individual,
    institutional, structural, and opportunistic factors.
    
    [3] ARGS (all documented)
    Args:
        story: Story to analyze with events and context
        context: Analysis context including actor profiles
        config: Optional configuration overrides
        timeout: Maximum execution time in seconds
    
    [4] RETURNS (always documented)
    Returns:
        MotivationResult containing analysis and metadata
    
    [5] RAISES (all exceptions documented)
    Raises:
        ValidationError: If story or context is invalid
        TimeoutError: If analysis exceeds timeout
        AnalysisError: If analysis fails after retries
    
    [6] EXAMPLE (for complex functions)
    Example:
        >>> result = await analyze_motivation(story, context)
        >>> print(result.synthesis.primary_driver)
    """
    # [7] EARLY VALIDATION
    if not story.events:
        raise ValidationError("Story must have at least one event")
    
    # [8] DEFAULTS
    config = config or AnalysisConfig()
    
    # [9] MAIN LOGIC (single level of abstraction)
    try:
        foundation = await _build_foundation(story, context)
        analysis = await _run_analysis(foundation, config)
        validated = await _validate_output(analysis)
        return MotivationResult(analysis=validated)
    except LLMError as e:
        raise AnalysisError(f"Analysis failed: {e}") from e
```

## 7.3 Class Structure

```python
# EVERY class follows this structure

class MotivationAnalysisAgent(BaseAgent[MotivationInput, MotivationOutput]):
    """
    [1] ONE-LINE SUMMARY
    Agent for four-layer motivation analysis.
    
    [2] DETAILED DESCRIPTION
    Analyzes motivations behind geopolitical events by examining
    individual, institutional, structural, and opportunistic factors.
    
    [3] ATTRIBUTES (class and instance)
    Attributes:
        task_name: Name of this agent's task
        version: Agent version for tracking
        default_tier: Default model tier for this agent
    
    [4] EXAMPLE
    Example:
        >>> agent = MotivationAnalysisAgent(router, validator, metrics)
        >>> result = await agent.run(input)
    """
    
    # [5] CLASS VARIABLES (with types)
    task_name: ClassVar[str] = "motivation_analysis"
    version: ClassVar[str] = "1.0.0"
    default_tier: ClassVar[ModelTier] = ModelTier.FRONTIER
    
    # [6] CONSTANTS
    MIN_ALTERNATIVES: ClassVar[int] = 2
    MAX_RETRIES: ClassVar[int] = 3
    
    # [7] __init__ (dependency injection)
    def __init__(
        self,
        router: ModelRouter,
        validator: OutputValidator,
        metrics: MetricsCollector,
        *,
        config: AgentConfig | None = None
    ) -> None:
        """Initialize agent with dependencies."""
        super().__init__(router, validator, metrics, config)
    
    # [8] PUBLIC METHODS (the interface)
    async def run(self, input: MotivationInput) -> AgentResult[MotivationOutput]:
        """Execute motivation analysis."""
        ...
    
    # [9] PRIVATE METHODS (implementation details)
    def _build_messages(self, input: MotivationInput) -> list[dict[str, str]]:
        """Build LLM messages."""
        ...
    
    def _parse_output(self, content: str) -> MotivationOutput:
        """Parse LLM output."""
        ...
    
    # [10] STATIC/CLASS METHODS (if any)
    @classmethod
    def from_config(cls, config: dict) -> "MotivationAnalysisAgent":
        """Create agent from configuration dict."""
        ...
```

---

# PART VIII: NAMING & STYLE

## 8.1 Naming Conventions

```python
# MANDATORY naming conventions

# CLASSES: PascalCase, noun phrases, descriptive
class MotivationAnalysisAgent:     # ✅ Clear purpose
class ChainMappingService:         # ✅ Clear purpose
class MAAgt:                       # ❌ Unclear abbreviation
class Utils:                       # ❌ Too generic

# FUNCTIONS/METHODS: snake_case, verb phrases, action-oriented
async def analyze_motivation():    # ✅ Clear action
async def build_context():         # ✅ Clear action
async def process():               # ❌ Too vague
async def do_stuff():              # ❌ Meaningless

# VARIABLES: snake_case, noun phrases, descriptive
article_count: int                 # ✅ Clear meaning
motivation_result: MotivationOutput # ✅ Clear type/purpose
cnt: int                          # ❌ Abbreviation
x: int                            # ❌ Meaningless
data: dict                        # ❌ Too generic

# CONSTANTS: SCREAMING_SNAKE_CASE
MAX_RETRY_ATTEMPTS = 3            # ✅
DEFAULT_TIMEOUT_SECONDS = 30.0    # ✅
max_retries = 3                   # ❌ Looks like variable

# PRIVATE: Single underscore prefix
def _internal_helper(self):       # ✅ Private method
_cache: dict                      # ✅ Private variable

# TYPE VARIABLES: PascalCase with T suffix
InputT = TypeVar("InputT")        # ✅
OutputT = TypeVar("OutputT")      # ✅
T = TypeVar("T")                  # ✅ (for generic single types)

# PROTOCOLS: Suffix with Protocol or -able
class Runnable(Protocol):         # ✅
class CacheableProtocol(Protocol): # ✅
class ICacheable(Protocol):       # ❌ Java-style I prefix
```

## 8.2 Import Organization

```python
# MANDATORY import organization (enforced by ruff)

# [1] Standard library imports
from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any, ClassVar, Generic, TypeVar
from uuid import UUID

# [2] Third-party imports
import structlog
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

# [3] Local imports (absolute, from package root)
from undertow.agents.base import BaseAgent, AgentResult
from undertow.core.quality import QualityGate
from undertow.llm.router import ModelRouter, ModelTier
from undertow.schemas.analysis import MotivationInput, MotivationOutput

# [4] Type checking only imports (for circular import prevention)
if TYPE_CHECKING:
    from undertow.services import ArticleService

# RULES:
# - Each group separated by blank line
# - Alphabetized within groups
# - No relative imports (always use absolute from package root)
# - No wildcard imports (from x import *)
```

## 8.3 String Formatting

```python
# MANDATORY string formatting rules

# ❌ FORBIDDEN: %-formatting
message = "Processing %s with %d items" % (name, count)

# ❌ FORBIDDEN: .format() for simple cases
message = "Processing {} with {} items".format(name, count)

# ✅ REQUIRED: f-strings for simple interpolation
message = f"Processing {name} with {count} items"

# ✅ REQUIRED: Structured logging (not string concatenation)
logger.info(
    "Processing started",
    name=name,
    count=count,
    story_id=str(story.id)
)

# ✅ REQUIRED: Template strings for long/complex strings
PROMPT_TEMPLATE = """
You are analyzing the following story:

**Headline:** {headline}
**Summary:** {summary}

Please provide your analysis.
"""

prompt = PROMPT_TEMPLATE.format(
    headline=story.headline,
    summary=story.summary
)
```

---

# PART IX: DOCUMENTATION STANDARDS

## 9.1 Docstring Requirements

```python
# EVERY public function/class MUST have docstrings

# Google-style docstrings (enforced by ruff)

def analyze_motivation(
    story: Story,
    context: AnalysisContext,
    *,
    config: AnalysisConfig | None = None
) -> MotivationResult:
    """
    Analyze motivations behind story events.
    
    Performs four-layer motivation analysis examining individual,
    institutional, structural, and opportunistic factors behind
    the events described in the story.
    
    Args:
        story: Story containing events to analyze. Must have at least
            one event with a valid timestamp.
        context: Analysis context containing actor profiles, historical
            context, and relevant background information.
        config: Optional configuration overrides. If not provided,
            defaults from settings are used.
    
    Returns:
        MotivationResult containing:
            - analysis: The four-layer motivation analysis
            - metadata: Execution metadata (timing, tokens, cost)
            - quality_score: Quality assessment (0-1)
    
    Raises:
        ValidationError: If story has no events or context is incomplete.
        AnalysisError: If LLM analysis fails after retries.
        TimeoutError: If analysis exceeds configured timeout.
    
    Example:
        >>> context = build_context(story)
        >>> result = await analyze_motivation(story, context)
        >>> print(result.analysis.synthesis.primary_driver)
        "layer1_individual"
    
    Note:
        This function uses FRONTIER tier models and typically takes
        30-60 seconds to complete. Consider using caching for
        repeated analyses of the same story.
    
    See Also:
        - `ChainMappingAgent`: For consequence chain analysis
        - `SubtletyAgent`: For signal/silence analysis
    """
    ...
```

## 9.2 Code Comments

```python
# COMMENT REQUIREMENTS

# [1] EXPLAIN WHY, not what (code shows what)
# ❌ Bad: Increment counter
counter += 1
# ✅ Good: Track retries for exponential backoff calculation
retry_count += 1

# [2] EXPLAIN COMPLEX LOGIC
# Confidence decay follows exponential model:
# - 1st order: full confidence
# - Each subsequent order: multiply by decay_factor (0.85)
# This reflects increasing uncertainty in longer causal chains
confidence = base_confidence * (decay_factor ** (order - 1))

# [3] DOCUMENT MAGIC NUMBERS
# 0.75 threshold based on empirical testing:
# - Below 0.75: High rate of quality gate failures
# - Above 0.75: Diminishing returns in accuracy
QUALITY_THRESHOLD = 0.75

# [4] EXPLAIN WORKAROUNDS
# WORKAROUND: Anthropic API returns inconsistent JSON escaping
# for certain Unicode characters. We normalize before parsing.
# TODO: Remove when Anthropic fixes this (tracked in ISSUE-123)
content = normalize_json_escaping(content)

# [5] MARK TODO/FIXME with tracking
# TODO(ISSUE-456): Implement caching for actor profiles
# FIXME(ISSUE-789): Handle rate limit errors gracefully
```

## 9.3 API Documentation

```python
# ALL API endpoints MUST have complete OpenAPI documentation

from fastapi import APIRouter, Path, Query, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()

class AnalyzeStoryRequest(BaseModel):
    """Request body for story analysis."""
    
    priority: Priority = Field(
        default=Priority.NORMAL,
        description="Queue priority for analysis job"
    )
    config_overrides: dict | None = Field(
        default=None,
        description="Optional configuration overrides"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "priority": "high",
                    "config_overrides": {"quality_threshold": 0.9}
                }
            ]
        }
    }

@router.post(
    "/stories/{story_id}/analyze",
    response_model=AnalysisJobResponse,
    status_code=202,
    summary="Trigger story analysis",
    description="""
    Triggers the full analysis pipeline for a story.
    
    The analysis runs asynchronously and progresses through four passes:
    1. **Foundation**: Factual reconstruction, context building, actor profiling
    2. **Core Analysis**: Motivation analysis, chain mapping, subtlety analysis
    3. **Verification**: Adversarial debate, fact-checking, source verification
    4. **Production**: Article writing, voice calibration, quality assessment
    
    Monitor progress via `GET /stories/{story_id}` or subscribe to webhooks.
    """,
    responses={
        202: {
            "description": "Analysis job queued successfully",
            "content": {
                "application/json": {
                    "example": {
                        "job_id": "550e8400-e29b-41d4-a716-446655440000",
                        "story_id": "550e8400-e29b-41d4-a716-446655440001",
                        "status": "queued",
                        "estimated_duration_minutes": 15
                    }
                }
            }
        },
        404: {"description": "Story not found"},
        409: {"description": "Analysis already in progress for this story"},
        503: {"description": "Analysis pipeline temporarily unavailable"}
    },
    tags=["analysis"]
)
async def analyze_story(
    story_id: UUID = Path(
        ...,
        description="Unique identifier of the story to analyze"
    ),
    request: AnalyzeStoryRequest = ...,
    service: AnalysisService = Depends()
) -> AnalysisJobResponse:
    """Trigger analysis pipeline for a story."""
    ...
```

---

# PART X: FORBIDDEN PATTERNS

## 10.1 Absolutely Forbidden

```python
"""
PATTERNS THAT WILL IMMEDIATELY BLOCK PR

These patterns indicate fundamental quality issues.
No exceptions. No "we'll fix it later."
"""

# ❌ FORBIDDEN: Any type
def process(data: Any) -> Any:
    ...

# ❌ FORBIDDEN: Bare except
try:
    risky()
except:
    pass

# ❌ FORBIDDEN: Catching Exception without re-raise
try:
    risky()
except Exception:
    log.error("failed")
    return None

# ❌ FORBIDDEN: Mutable default arguments
def process(items: list = []):
    items.append(something)

# ❌ FORBIDDEN: Global mutable state
GLOBAL_CACHE = {}
def add_to_cache(key, value):
    GLOBAL_CACHE[key] = value

# ❌ FORBIDDEN: Magic strings/numbers
if status == "active":  # Use enum
if threshold > 0.75:    # Use named constant

# ❌ FORBIDDEN: Nested functions beyond 2 levels
def outer():
    def middle():
        def inner():  # Too deep
            ...

# ❌ FORBIDDEN: God classes (>300 lines)
class DoEverything:
    # 500+ lines of methods

# ❌ FORBIDDEN: Functions with >7 parameters
def process(a, b, c, d, e, f, g, h):
    ...

# ❌ FORBIDDEN: Wildcard imports
from module import *

# ❌ FORBIDDEN: Relative imports
from ..utils import helper

# ❌ FORBIDDEN: Print statements (use logging)
print("Debug:", value)

# ❌ FORBIDDEN: TODO without issue tracking
# TODO: fix this later

# ❌ FORBIDDEN: Commented-out code
# old_function()
# more_old_code()

# ❌ FORBIDDEN: String concatenation for SQL
query = "SELECT * FROM users WHERE id = " + user_id

# ❌ FORBIDDEN: Hardcoded secrets
API_KEY = "sk-1234567890"
```

## 10.2 Code Smells (Require Justification)

```python
"""
PATTERNS REQUIRING EXPLICIT JUSTIFICATION

These may be acceptable in specific cases but require
explanation in PR description.
"""

# ⚠️ SMELL: isinstance checks (prefer duck typing)
if isinstance(obj, SpecificClass):
    ...
# ACCEPTABLE WHEN: Type narrowing for Union types

# ⚠️ SMELL: hasattr checks
if hasattr(obj, "method"):
    ...
# ACCEPTABLE WHEN: Working with external/untyped code

# ⚠️ SMELL: Type: ignore comments
result = untyped_function()  # type: ignore
# ACCEPTABLE WHEN: External library without stubs, with TODO to fix

# ⚠️ SMELL: Protected member access
obj._internal_method()
# ACCEPTABLE WHEN: Testing private methods, with explanation

# ⚠️ SMELL: Long functions (>30 lines)
# ACCEPTABLE WHEN: Single logical operation, with explanation

# ⚠️ SMELL: Deep nesting (>3 levels)
# ACCEPTABLE WHEN: Unavoidable complex logic, with explanation
```

---

# PART XI: REQUIRED PATTERNS

## 11.1 Always Required

```python
"""
PATTERNS THAT MUST ALWAYS BE USED

Absence of these patterns will block PR.
"""

# ✅ REQUIRED: Type annotations on everything
async def process(article: Article) -> ProcessResult:
    ...

# ✅ REQUIRED: Explicit return types (even None)
def configure() -> None:
    ...

# ✅ REQUIRED: Pydantic for data classes
class Config(BaseModel):
    ...

# ✅ REQUIRED: Structured logging
logger.info("event_name", key1=value1, key2=value2)

# ✅ REQUIRED: Context managers for resources
async with get_session() as session:
    ...

# ✅ REQUIRED: Dependency injection
def __init__(self, service: Service) -> None:
    self.service = service

# ✅ REQUIRED: Enums for fixed choices
class Status(Enum):
    PENDING = "pending"
    ACTIVE = "active"

# ✅ REQUIRED: Named constants
QUALITY_THRESHOLD = 0.75
MAX_RETRIES = 3

# ✅ REQUIRED: Dataclasses/NamedTuples for data containers
@dataclass(frozen=True)
class Point:
    x: float
    y: float

# ✅ REQUIRED: async/await for I/O operations
result = await fetch_data()

# ✅ REQUIRED: Explicit None checks
if value is None:
    ...

# ✅ REQUIRED: Early returns
if not valid:
    return Error("invalid")
# Continue with valid case...
```

## 11.2 Agent-Specific Requirements

```python
"""
PATTERNS REQUIRED FOR ALL AGENTS
"""

# ✅ REQUIRED: Inherit from BaseAgent
class MyAgent(BaseAgent[InputT, OutputT]):
    ...

# ✅ REQUIRED: Define class variables
task_name: ClassVar[str] = "my_task"
version: ClassVar[str] = "1.0.0"
input_schema: ClassVar[type] = MyInput
output_schema: ClassVar[type] = MyOutput

# ✅ REQUIRED: Implement abstract methods
def _build_messages(self, input: InputT) -> list[dict]:
    ...

def _parse_output(self, content: str) -> OutputT:
    ...

async def _assess_quality(self, output: OutputT, input: InputT) -> float:
    ...

# ✅ REQUIRED: Return AgentResult (not raw output)
async def run(self, input: InputT) -> AgentResult[OutputT]:
    ...

# ✅ REQUIRED: Validate output against schema
validated = self.validator.validate(output, self.output_schema)

# ✅ REQUIRED: Record metrics
self.metrics.record_execution(...)

# ✅ REQUIRED: Structured logging in agents
logger.info(
    "agent_execution_complete",
    agent=self.task_name,
    duration_ms=duration,
    quality_score=score
)
```

---

# PART XII: REVIEW ENFORCEMENT

## 12.1 Automated Checks (CI)

```yaml
# .github/workflows/quality.yml

name: Quality Gates

on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Ruff lint
        run: ruff check src/ tests/ --output-format=github
      
      - name: Ruff format
        run: ruff format --check src/ tests/
      
      - name: MyPy (strict)
        run: mypy src/ --strict
      
      - name: Import linter
        run: lint-imports
      
      - name: Bandit security
        run: bandit -r src/ -c pyproject.toml
      
      - name: Complexity check
        run: radon cc src/ --min C --total-average
        
      - name: Docstring coverage
        run: interrogate src/ --fail-under 100

  test:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      
      - name: Run tests with coverage
        run: |
          pytest tests/ \
            --cov=src/undertow \
            --cov-report=xml \
            --cov-fail-under=85
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## 12.2 Code Review Checklist

```markdown
# MANDATORY CODE REVIEW CHECKLIST

Before approving ANY PR, verify ALL items:

## Architecture
- [ ] Follows layered architecture
- [ ] No forbidden imports (checked by CI)
- [ ] New dependencies justified
- [ ] No circular dependencies

## Type Safety
- [ ] All functions have complete type annotations
- [ ] No `Any` types without justification
- [ ] Pydantic models for all data structures
- [ ] No type: ignore without justification

## Error Handling
- [ ] No bare except clauses
- [ ] All exceptions logged with context
- [ ] Custom exceptions inherit from UndertowError
- [ ] Error messages are actionable

## Testing
- [ ] Tests for all new public functions
- [ ] Coverage meets thresholds (checked by CI)
- [ ] Tests are deterministic (no flakiness)
- [ ] Golden tests for agents

## Documentation
- [ ] All public functions have docstrings
- [ ] Complex logic has explanatory comments
- [ ] API changes documented in OpenAPI
- [ ] README updated if needed

## Agents (if applicable)
- [ ] Inherits from BaseAgent
- [ ] Class variables defined
- [ ] Abstract methods implemented
- [ ] Output validated against schema
- [ ] Quality assessment implemented
- [ ] Metrics recorded

## Quality
- [ ] No code smells without justification
- [ ] No magic numbers/strings
- [ ] No commented-out code
- [ ] Functions ≤50 lines
- [ ] Classes ≤300 lines

## Security
- [ ] No hardcoded secrets
- [ ] Input validation present
- [ ] SQL parameterized
- [ ] No path traversal vulnerabilities
```

## 12.3 PR Template

```markdown
# Pull Request

## Description
<!-- What does this PR do? -->

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Refactoring
- [ ] Documentation
- [ ] Testing

## Checklist
- [ ] My code follows the coding standards
- [ ] I have performed a self-review
- [ ] I have added tests
- [ ] I have updated documentation
- [ ] All CI checks pass

## Architecture Impact
<!-- Does this change the architecture? If yes, explain. -->

## Agent Changes (if applicable)
- [ ] Agent follows BaseAgent contract
- [ ] Output schema is validated
- [ ] Quality assessment is implemented
- [ ] Golden tests added/updated

## Justifications (if any)
<!-- Explain any code smells or exceptions to standards -->
```

---

# APPENDIX: QUICK REFERENCE

## Enforcement Summary

| Category | Enforcement | Blocking |
|----------|-------------|----------|
| Type annotations | MyPy strict | Yes |
| Code style | Ruff | Yes |
| Imports | import-linter | Yes |
| Test coverage | pytest-cov (85%) | Yes |
| Docstrings | interrogate (100%) | Yes |
| Complexity | radon (CC ≤ 10) | Yes |
| Security | bandit | Yes |
| Architecture | Code review | Yes |
| Agent contract | Code review | Yes |

## Key Limits

| Metric | Limit |
|--------|-------|
| Lines per file | 500 |
| Lines per function | 50 |
| Lines per class | 300 |
| Parameters per function | 7 |
| Nesting depth | 4 |
| Import depth | 4 |
| Cyclomatic complexity | 10 |

---

*Zero tolerance means zero tolerance. No exceptions. No "temporary" violations. Quality is not negotiable.*

