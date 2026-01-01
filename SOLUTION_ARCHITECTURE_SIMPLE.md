# The Undertow - Simplified Architecture

## Overview

A fully automated geopolitical intelligence system that produces a daily newsletter. Runs autonomously with no human intervention required.

**Target Cost: ~$1/day**

---

## System Design

### Single-Server Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AWS Lightsail ($10/mo)                   │
│                                                             │
│  ┌─────────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │   Python    │    │  PostgreSQL  │    │    Redis     │   │
│  │   Runner    │───▶│   Database   │    │   (simple)   │   │
│  └─────────────┘    └──────────────┘    └──────────────┘   │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Simple Pipeline Orchestrator             │   │
│  │  1. Select Stories   (~$0.01)                        │   │
│  │  2. Analyze + Write  (~$0.15/article × 5)            │   │
│  │  3. Send Newsletter  (free)                          │   │
│  └─────────────────────────────────────────────────────┘   │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              External Services                        │   │
│  │  • Anthropic API (Claude Haiku) - ~$0.90/day         │   │
│  │  • Gmail SMTP (email) - Free (500/day)               │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Daily Schedule

**All times in Singapore Time (SGT = UTC+8)**

| Time (SGT) | Time (UTC) | Activity |
|------------|------------|----------|
| 4:30 AM | 8:30 PM (prev day) | Pipeline starts |
| 4:30-4:35 | - | Story selection |
| 4:35-5:15 | - | Article generation (5 articles) |
| 5:15-5:20 | - | Newsletter assembly |
| 5:20 AM | 9:20 PM | **Newsletter delivered** |

**Total runtime: ~50 minutes**

---

## Cost Breakdown

### AI Costs (Claude 3.5 Haiku)

| Operation | Input Tokens | Output Tokens | Cost |
|-----------|--------------|---------------|------|
| Story selection | 2,000 | 1,500 | $0.002 |
| Analysis + Writing (per article) | 3,000 | 4,000 | $0.006 |
| Light editing (per article) | 4,000 | 4,000 | $0.006 |
| **Per article total** | - | - | **$0.012** |
| **5 articles** | - | - | **$0.060** |

**Note**: Claude Haiku pricing: $0.25/1M input, $1.25/1M output

Wait, let me recalculate with more realistic token counts:

### Revised AI Costs

| Operation | Input Tokens | Output Tokens | Cost |
|-----------|--------------|---------------|------|
| Story selection | 5,000 | 3,000 | $0.005 |
| Analysis + Writing (per article) | 8,000 | 8,000 | $0.012 |
| Light editing (per article) | 10,000 | 8,000 | $0.013 |
| **Per article total** | - | - | **$0.025** |
| **5 articles** | - | - | **$0.125** |

**But wait** - using GPT-4o-mini is actually cheaper:
- $0.15/1M input, $0.60/1M output

| Operation | Input Tokens | Output Tokens | Cost |
|-----------|--------------|---------------|------|
| Story selection | 5,000 | 3,000 | $0.003 |
| Analysis + Writing (per article) | 8,000 | 8,000 | $0.006 |
| Light editing (per article) | 10,000 | 8,000 | $0.006 |
| **Per article total** | - | - | **$0.012** |
| **5 articles** | - | - | **$0.06** |

### Realistic Daily Cost

With some buffer for retries and variations:

| Item | Cost |
|------|------|
| AI (5 articles) | $0.10 - $0.30 |
| Buffer for retries | $0.10 |
| **Daily AI cost** | **~$0.20 - $0.40** |

### Monthly Cost

| Item | Monthly |
|------|---------|
| AWS Lightsail | $10 |
| Anthropic/OpenAI | $10-15 |
| Gmail SMTP | Free (500/day) |
| **Total** | **~$20-25/month** |

---

## Model Selection

Using the cheapest effective models:

| Task | Model | Why |
|------|-------|-----|
| Story Selection | GPT-4o-mini | Cheapest, good at ranking |
| Analysis + Writing | Claude 3.5 Haiku | Best quality/price for writing |
| Editing | GPT-4o-mini | Simple task, cheapest |

---

## Pipeline Stages

### Stage 1: Story Selection (~1 min)
- Fetch headlines from RSS feeds
- LLM ranks by significance
- Select top 5 stories
- Cost: ~$0.01

### Stage 2: Article Generation (~8 min per article)
For each story:
1. **Combined Analysis Prompt**: Single prompt that asks for:
   - 4-layer motivation analysis
   - Chain mapping to 4th order
   - Subtlety decoding
   - Full article with proper structure
2. **Light Edit**: Quick pass for style fixes
- Cost: ~$0.03-0.05 per article

### Stage 3: Newsletter Assembly (~1 min)
- Combine articles into newsletter format
- Generate preamble
- Cost: ~$0.01

### Stage 4: Send (~1 min)
- Send via Gmail SMTP
- Cost: Free (500 emails/day limit)

**Total: ~50 minutes, ~$0.20-0.40**

---

## No Human Review

The system auto-publishes without human review because:

1. **Quality is consistent**: Using well-tested prompts
2. **Cost matters**: Human review infrastructure adds complexity
3. **Speed matters**: Newsletter must be ready by 4:30 AM SGT
4. **Low stakes**: Can always send corrections

If an article fails quality checks, it's simply skipped (newsletter goes out with 4 articles instead of 5).

---

## No Caching

Caching is removed because:
1. **Complexity**: Adds infrastructure overhead
2. **Cost**: Daily content is always new anyway
3. **Freshness**: We want today's analysis, not cached content

---

## No Observability Stack

Simplified monitoring:
- **Logs**: Written to systemd journal (free)
- **Errors**: Email alert if pipeline fails
- **Costs**: Tracked in simple SQLite/file

No Prometheus, Grafana, etc. needed.

---

## Database Schema (Minimal)

```sql
-- Just what we need
CREATE TABLE articles (
    id UUID PRIMARY KEY,
    headline TEXT NOT NULL,
    content TEXT NOT NULL,
    zones TEXT[],
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE pipeline_runs (
    id UUID PRIMARY KEY,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    article_count INT,
    total_cost DECIMAL(10,4),
    status TEXT
);
```

---

## File Structure (Simplified)

```
undertow/
├── src/undertow/
│   ├── runner.py              # Main entry point
│   ├── config.py              # Configuration
│   ├── core/
│   │   └── simple_orchestrator.py  # Pipeline logic
│   ├── llm/
│   │   └── router.py          # LLM calls
│   └── services/
│       └── newsletter.py      # Email sending
├── requirements.txt
├── .env
└── alembic/                   # Database migrations
```

---

## Getting Started

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for step-by-step instructions.

---

## Summary

| Aspect | Decision |
|--------|----------|
| **Cost** | ~$0.30/day AI, ~$25/month total |
| **Infrastructure** | Single AWS Lightsail server |
| **Human Review** | None - fully automated |
| **Caching** | None - not needed |
| **Monitoring** | Logs only |
| **Schedule** | 4:30 AM SGT start → 5:20 AM SGT newsletter |

