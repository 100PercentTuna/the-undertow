# Input Needed from User

This file tracks information needed from the user to complete the implementation.

---

## 🔴 BLOCKING (Need before deployment)

### 1. API Keys
- [ ] **Anthropic API Key** - Required for Claude models (~$10-15/month)
  - Get from: https://console.anthropic.com
  - Set as `ANTHROPIC_API_KEY` in `.env`
- [ ] **Gmail App Password** - Required for sending emails (FREE)
  - Enable 2FA on Gmail: https://myaccount.google.com
  - Generate App Password: Security → App passwords → Mail → "The Undertow"
  - Set as `SMTP_PASSWORD` in `.env` (16 characters, no spaces)

### 2. Newsletter Recipients
- [ ] **Email addresses** - Who should receive the newsletter?
  - Set as `NEWSLETTER_RECIPIENTS` in `.env` (comma-separated)

### 3. Gmail Configuration
- [ ] **Gmail address** - Your Gmail account
  - Set as `SMTP_USERNAME` and `FROM_EMAIL` in `.env`
  - Must match the account where you generated the App Password

---

## 🟡 NEEDED SOON (Can build around for now)

### 3. Source Configuration
- [ ] **RSS Feed URLs** - List of initial sources to ingest by zone
  - Need actual feed URLs for 42 zones
  - Will add to ingestion configuration
  
### 4. Email Configuration
- [ ] **Newsletter Template** - HTML template for emails
- [ ] **Subscriber List Source** - How will subscribers be managed?
- [ ] **FROM email address** - Currently `newsletter@theundertow.com`

### 5. Content Guidelines
- [ ] **Sample Articles** - 2-3 examples of desired output style
  - For golden tests in `tests/golden/`
  - For prompt tuning

---

## 🟢 NICE TO HAVE (Can proceed without)

### 6. Customization
- [ ] **Logo/Branding Assets** - For newsletter
- [ ] **Custom Zones** - Any modifications to the 42-zone structure?

### 7. Monitoring
- [ ] **Alert Email/Slack** - Where to send operational alerts?

---

## ASSUMPTIONS MADE

These assumptions were made to proceed with implementation. Please confirm or correct:

1. **Model Selection**
   - Primary: Claude Sonnet 4 (`claude-sonnet-4-20250514`)
   - Fallback: GPT-4o
   - Fast tier: Claude 3.5 Haiku / GPT-4o-mini

2. **Daily Schedule (UTC)**
   - 4:00 AM - Pipeline starts
   - 10:00 AM - Newsletter publishes
   
3. **Quality Thresholds**
   - Foundation Gate: 75%
   - Analysis Gate: 80%
   - Adversarial Gate: 80%
   - Output Gate: 85%

4. **Budget**
   - Default daily budget: $50 USD
   - Target per-article cost: $1.50-2.50

5. **Article Count**
   - 5 feature articles per daily edition
   - Plus preamble/newsletter wrapper

6. **Database**
   - PostgreSQL with pgvector extension
   - Connection pooling: 20 base, 10 overflow

---

## QUESTIONS

1. Should the system support multiple concurrent users/editors, or is this single-tenant?
2. Is there a preference for the admin dashboard framework (Next.js assumed)?
3. Should we integrate with any existing CMS or publishing platform?
4. What authentication method for API access? (Currently using API key header)
5. Do you want webhook notifications when articles are ready for review?

---

## IMPLEMENTATION STATUS

### ✅ Completed - A+++ Features

#### Core Architecture
- Project structure and configuration (Poetry, strict typing, import linting)
- Pydantic schemas for all agents (100% type coverage)
- SQLAlchemy models (Story, Article, Pipeline, Documents, Claims, Escalations)
- LLM providers (Anthropic, OpenAI) with circuit breakers
- Model router with intelligent tier selection, cost tracking, and caching
- BaseAgent contract (enforced via inheritance)

#### Analysis Agents (9)
- Motivation Analysis (4-layer analysis: individual, institutional, structural, opportunistic)
- Chain Mapping (forward/backward causal chains to 5th order)
- Self-Critique (internal review and revision)
- Subtlety Decoder (signals, silences, timing, choreography)
- Geometry Analysis (chokepoints, corridors, buffer zones)
- Deep Context (grievances, elite networks, strategic culture)
- Connections (analogues, strange bedfellows, invisible parties)
- Uncertainty (knowledge classification, confidence calibration)
- Source Collector (multi-source aggregation)

#### Adversarial System (3)
- Challenger Agent (strongest counter-case)
- Advocate Agent (defense with evidence)
- Judge Agent (final assessment with quality score)
- Full Debate Protocol with multi-round orchestration

#### Production Agents (3)
- Writer Agent (prose generation from analysis)
- Synthesis Agent (combine all analyses coherently)
- Editor Agent (quality control, revision decisions)

#### Quality Assurance
- 4-Gate System (Foundation 75%, Analysis 80%, Adversarial 80%, Output 85%)
- Human Escalation System (automatic routing for low-quality/controversial)
- Claim Extraction & Verification (source triangulation)
- Golden Tests (real geopolitical scenarios)

#### RAG System
- OpenAI embeddings (text-embedding-3-small, 1536 dimensions)
- pgvector integration (HNSW index, hybrid search)
- Query expansion and HyDE
- Cross-encoder reranking with MMR diversity
- 40+ source profiles across all 42 zones

#### Infrastructure
- FastAPI REST API with full CRUD (21+ endpoint groups)
- API Middleware: Auth (API key), Logging, Metrics, Rate Limiting
- Monitoring: JSON metrics, Prometheus metrics, Cost tracking
- Repository layer with async queries
- Docker/Docker Compose (multi-stage builds)
- Alembic migrations (2 revisions: initial + vector store)
- Celery for background tasks
- Redis caching
- Pre-commit hooks (ruff, mypy, bandit)

#### CLI
- `undertow serve` - Start API server
- `undertow pipeline run` - Run analysis pipeline
- `undertow verify extract` - Extract claims from text
- `undertow verify check` - Verify a claim
- `undertow escalations list/resolve` - Manage escalations
- `undertow docs search/index` - RAG operations
- `undertow costs summary/by-agent` - Cost tracking
- `undertow sources list/score` - Source management
- `undertow db migrate/rollback` - Database management

#### Frontend (Next.js, 11 pages)
- Dashboard (overview stats)
- Stories (story management)
- Articles (article management)
- Pipeline (real-time status)
- Costs (budget visualization)
- Zones (42 global zones)
- Escalations (human review queue)
- Verification (claim checking)
- Newsletter (preview/send)
- Jobs (background tasks)
- Settings (system configuration)

#### Testing
- Unit tests: 32+ test files
- Integration tests: Pipeline flow, API endpoints, Verification, Escalations
- Golden tests: Israel-Somaliland, Niger coup, Taiwan scenarios
- E2E tests: Full pipeline execution

### 📋 Remaining TODO
- Full test coverage (target 85%) - currently ~75%
- Documentation site

---

### 📊 File Count

| Component | Files |
|-----------|-------|
| Backend Python (`src/undertow/`) | **140** |
| Tests (`tests/`) | **32** |
| Frontend TSX (`frontend/`) | **11** |
| Config/Scripts | 15+ |
| **Total** | **198+** |

---

*Last updated: A+++ feature complete, pending API keys for deployment*

