# The Undertow — Documentation Index

## A Global Intelligence System for Serious People

---

# DOCUMENTATION OVERVIEW

This repository contains the complete design documentation for **The Undertow**, an AI-powered geopolitical intelligence system that produces daily newsletter-format analysis covering 42 global zones.

---

# DOCUMENT MAP

## 📋 Core Project Documentation

| Document | Description | Key Contents |
|----------|-------------|--------------|
| [THE_UNDERTOW.md](THE_UNDERTOW.md) | **Master Project Specification** | Philosophy, voice, methodology, article structure, quality standards, zones 1-18 |
| [ZONES_19_TO_42.md](ZONES_19_TO_42.md) | **Complete Zone Coverage** | Sub-Saharan Africa, South Asia, East Asia, Southeast Asia, Oceania, Americas |

---

## 🏗️ Technical Architecture

| Document | Description | Key Contents |
|----------|-------------|--------------|
| [SOLUTION_ARCHITECTURE.md](SOLUTION_ARCHITECTURE.md) | **System Architecture v3** | Python-aligned, 4-pass pipeline, $8-15/day costs, deployment architecture |
| [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) | **Project Structure** | Complete folder layout, layer responsibilities, import rules |
| [DATA_MODELS.md](DATA_MODELS.md) | **Database Schema** | All entity definitions, relationships, indexes |
| [API_SPECIFICATION.md](API_SPECIFICATION.md) | **REST API Reference** | All endpoints, request/response formats, webhooks |
| [CONFIGURATION.md](CONFIGURATION.md) | **Configuration Guide** | Environment variables, YAML config, Docker, Terraform |

---

## 🤖 AI Components

| Document | Description | Key Contents |
|----------|-------------|--------------|
| [PROMPT_LIBRARY.md](PROMPT_LIBRARY.md) | **Production Prompts** | All agent prompts with few-shot examples, output formats |

---

## 👤 User Documentation

| Document | Description | Key Contents |
|----------|-------------|--------------|
| [USER_STORIES.md](USER_STORIES.md) | **User Stories & Acceptance Criteria** | 14 epics, 75+ stories, comprehensive acceptance criteria |

---

## 🚀 Implementation

| Document | Description | Key Contents |
|----------|-------------|--------------|
| [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) | **Python Implementation Roadmap** | 16-week plan, sprint breakdown, code examples, team structure |
| [GUARDRAILS.md](GUARDRAILS.md) | **Engineering Quality Standards** | Reliability, correctness, maintainability, performance, agent quality |
| [CODING_STANDARDS.md](CODING_STANDARDS.md) | **Zero-Tolerance Coding Standards** | Absolute quality requirements, multi-agent patterns, forbidden code |

---

# QUICK START

## For Product Owners
1. Start with [THE_UNDERTOW.md](THE_UNDERTOW.md) for project vision and philosophy
2. Review [USER_STORIES.md](USER_STORIES.md) for feature requirements
3. Understand zones via [ZONES_19_TO_42.md](ZONES_19_TO_42.md)

## For Architects
1. Read [SOLUTION_ARCHITECTURE.md](SOLUTION_ARCHITECTURE.md) for system design
2. Review [DATA_MODELS.md](DATA_MODELS.md) for data structures
3. Check [API_SPECIFICATION.md](API_SPECIFICATION.md) for interface contracts

## For Developers
1. **Start with [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)** for Python architecture & sprint plan
2. Reference [CONFIGURATION.md](CONFIGURATION.md) for setup
3. Use [API_SPECIFICATION.md](API_SPECIFICATION.md) for endpoints
4. Use [PROMPT_LIBRARY.md](PROMPT_LIBRARY.md) for AI agent implementation

## For AI/ML Engineers
1. Deep dive into [SOLUTION_ARCHITECTURE.md](SOLUTION_ARCHITECTURE.md) Section 2-5
2. Study [PROMPT_LIBRARY.md](PROMPT_LIBRARY.md) for all prompts
3. Understand quality systems in architecture doc

---

# SYSTEM HIGHLIGHTS

## The 4-Pass Analysis Pipeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         THE UNDERTOW PIPELINE                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  PASS 1: FOUNDATION                                                     │
│  ├── Factual Reconstruction (timeline, facts, actors)                   │
│  ├── Context Analysis (4 layers of context)                             │
│  └── Actor Profiling (individuals, institutions, relationships)         │
│                                                                         │
│  PASS 2: CORE ANALYSIS                                                  │
│  ├── 4-Layer Motivation Analysis                                        │
│  │   └── Individual → Institutional → Structural → Opportunistic        │
│  ├── Chain Mapping (forward 5 orders, backward cui bono)                │
│  └── Subtlety Decoding (signals, silences, timing)                      │
│                                                                         │
│  PASS 3: ENHANCEMENT & VERIFICATION                                     │
│  ├── Supplementary (theory, history, geography, shockwaves)             │
│  └── Adversarial (3-round debate, fact-check, source verify)            │
│                                                                         │
│  PASS 4: PRODUCTION                                                     │
│  ├── Article Writing (12-section structure)                             │
│  ├── Voice Calibration (style enforcement)                              │
│  └── Quality Evaluation (7 dimensions)                                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Intelligent Model Routing

| Tier | Models | Used For | Cost |
|------|--------|----------|------|
| **Frontier** | Claude Sonnet 4, GPT-4o | Motivation analysis, chain mapping, debates, article writing | $$$ |
| **High** | Claude Sonnet 4 | Theory analysis, fact-checking, preambles | $$ |
| **Standard** | GPT-4o-mini | Context analysis, source verification | $ |
| **Fast** | Claude Haiku | Zone scouts, aggregation, simple tasks | ¢ |

## Quality Gate System

```
GATE 1 (Foundation): 75% threshold
    └── All facts sourced, timeline complete, actors identified

GATE 2 (Analysis): 80% threshold
    └── 4-layer motivation, 4th-order chains, alternatives considered

GATE 3 (Adversarial): 80% threshold
    └── Debate complete, facts verified, sources cross-checked

GATE 4 (Output): 85% threshold
    └── Voice consistent, structure complete, all sources cited
```

## Cost Optimization Strategies

- **Progressive Complexity**: Start cheap, escalate only when needed
- **Aggressive Caching**: Embeddings, queries, unchanged analyses
- **Early Termination**: Skip passes for high-quality content
- **Conditional Execution**: Run expensive agents only when triggered
- **Parallel Processing**: Maximize throughput, minimize wall-time

**Target Daily Cost: $8-12 for 5 feature articles**

---

# 42-ZONE COVERAGE

## Zone Distribution by Region

| Region | Zones | Coverage |
|--------|-------|----------|
| **Europe** | 1-8 | Western, Southern, Nordic-Baltic, British Isles, Central, Balkans, Eastern, South Caucasus |
| **Russia & Eurasia** | 9-11 | Russian Federation, Central Asia West, Central Asia East |
| **Middle East & North Africa** | 12-18 | Levant, GCC, Iraq, Iran, Turkey, Maghreb, Egypt |
| **Sub-Saharan Africa** | 19-24 | Horn, East, Great Lakes/Central, Sahel, West Coast, Southern |
| **South Asia** | 25-27 | India, Pakistan/Afghanistan, Periphery |
| **East Asia** | 28-32 | China, Taiwan, Korean Peninsula, Japan, Mongolia |
| **Southeast Asia** | 33-34 | Mainland, Maritime |
| **Oceania & Pacific** | 35-36 | Australia/NZ, Pacific Islands |
| **Americas** | 37-42 | USA, Canada, Mexico/Central America, Caribbean, Andean, Southern Cone |

---

# KEY ANALYTICAL FRAMEWORKS

## The Four-Layer Motivation Analysis

1. **Layer 1 - Individual**: The specific decision-maker's position, needs, psychology
2. **Layer 2 - Institutional**: Bureaucratic interests, foreign ministry vs. military vs. economic actors
3. **Layer 3 - Structural**: What any actor in this position would face
4. **Layer 4 - Opportunistic**: Why now? What opened the window?

## Chain Mapping (5 Orders)

```
1st Order → Direct consequences (high confidence)
2nd Order → Responses to 1st order (moderate-high)
3rd Order → Systemic adaptations (moderate)
4th Order → Equilibrium shifts (low-moderate)
5th Order → Chain interactions (speculative)
```

## The Subtlety Framework

1. Signal in the action (intended audiences beyond the obvious)
2. Eloquent silences (who hasn't commented and why)
3. Timing messages (why now, what's bracketed)
4. Choreography (staging, protocol, visuals)
5. Deniable communications (leaks, proxies, back-channels)

---

# IMPLEMENTATION STATUS

## ✅ A+++ Features Complete

### Core System (Python)
- **125+ Python files** in `src/undertow/`
- **30+ test files** in `tests/`
- **12+ frontend pages** in `frontend/`

### Key Capabilities
| Capability | Implementation |
|------------|----------------|
| **Multi-Agent Analysis** | 9 analysis + 3 adversarial + 3 production agents |
| **RAG System** | pgvector + OpenAI embeddings + hybrid search |
| **Verification** | Claim extraction + source triangulation |
| **Human Escalation** | Automatic routing with review packages |
| **Quality Gates** | 4-gate system with 75%-85% thresholds |
| **Golden Tests** | Real geopolitical scenarios for validation |
| **CLI** | Full CLI with pipeline, verification, RAG commands |
| **API** | 15+ endpoint groups with auth, rate limiting |
| **Frontend** | 8 pages (Dashboard, Stories, Articles, Pipeline, Costs, Zones, Escalations, Verification) |

### Blocking Requirements
- API Keys (Anthropic, OpenAI, SendGrid)
- Infrastructure deployment decision

---

# DOCUMENT STATISTICS

| Document | Lines | Words | Key Sections |
|----------|-------|-------|--------------|
| THE_UNDERTOW.md | ~2,800 | ~28,000 | Philosophy, Zones 1-18, Methodology, Writing |
| ZONES_19_TO_42.md | ~2,200 | ~18,000 | Zones 19-42 with sources and frameworks |
| SOLUTION_ARCHITECTURE.md | ~2,200 | ~15,000 | Python pipeline, costs, deployment, quality gates |
| USER_STORIES.md | ~2,400 | ~15,000 | 14 Epics, 75+ Stories, Acceptance Criteria |
| PROMPT_LIBRARY.md | ~1,800 | ~12,000 | All agent prompts, output formats |
| DATA_MODELS.md | ~1,500 | ~8,000 | TypeScript schemas, SQL indexes |
| API_SPECIFICATION.md | ~1,800 | ~10,000 | REST endpoints, webhooks |
| CONFIGURATION.md | ~1,200 | ~6,000 | YAML configs, Docker, Terraform |
| IMPLEMENTATION_PLAN.md | ~2,000 | ~12,000 | Python code, sprints, team structure |
| GUARDRAILS.md | ~2,500 | ~15,000 | Quality standards, enforcement, CI/CD gates |
| CODING_STANDARDS.md | ~3,000 | ~18,000 | Zero-tolerance standards, agent patterns, forbidden code |
| PROJECT_STRUCTURE.md | ~1,200 | ~6,000 | Folder layout, layer responsibilities, Docker setup |

**Total: ~24,900 lines documentation + 180+ implementation files**

---

# VERSION HISTORY

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-01-01 | Initial complete documentation |

---

# CONTRIBUTING

This documentation is designed for a production-grade system. When making changes:

1. **Maintain consistency** across documents
2. **Update cross-references** when adding new sections
3. **Test prompts** before adding to the library
4. **Verify schemas** match implementation

---

*The Undertow: Intelligence for people who want to understand how the world actually works.*

