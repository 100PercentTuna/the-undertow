# The Undertow — API Specification

## RESTful API Endpoints

**Base URL:** `https://api.theundertow.io/v1`  
**Authentication:** Bearer token (JWT)  
**Rate Limiting:** 100 requests/minute per API key

---

# SECTION 1: AUTHENTICATION

## POST /auth/login

Login and receive JWT token.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "***",
  "mfa_code": "123456"  // Optional, required if MFA enabled
}
```

**Response 200:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "expires_in": 3600,
  "token_type": "Bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "name": "John Smith",
    "role": "EDITOR"
  }
}
```

**Response 401:**
```json
{
  "error": "invalid_credentials",
  "message": "Invalid email or password"
}
```

---

## POST /auth/refresh

Refresh access token.

**Request Body:**
```json
{
  "refresh_token": "eyJ..."
}
```

**Response 200:**
```json
{
  "access_token": "eyJ...",
  "expires_in": 3600
}
```

---

## POST /auth/logout

Invalidate tokens.

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Response 204:** No content

---

# SECTION 2: SOURCES

## GET /sources

List all sources with optional filters.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `tier` | integer | Filter by tier (1-4) |
| `zone` | string | Filter by zone coverage |
| `type` | string | RSS, API, or SCRAPER |
| `active` | boolean | Filter by active status |
| `page` | integer | Page number (default: 1) |
| `per_page` | integer | Items per page (default: 50, max: 200) |

**Response 200:**
```json
{
  "data": [
    {
      "id": "uuid",
      "name": "Financial Times",
      "url": "https://ft.com",
      "type": "RSS",
      "tier": 2,
      "zones": ["western_europe", "british_isles", "usa"],
      "reliability_score": 0.92,
      "active": true,
      "last_fetch_at": "2025-01-01T08:00:00Z",
      "last_fetch_status": "SUCCESS"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total_items": 312,
    "total_pages": 7
  }
}
```

---

## POST /sources

Create a new source.

**Request Body:**
```json
{
  "name": "Source Name",
  "url": "https://example.com",
  "type": "RSS",
  "tier": 2,
  "zones": ["horn_africa", "east_africa"],
  "languages": ["en"],
  "refresh_interval_minutes": 60,
  "bias_indicators": {
    "political_lean": "center",
    "state_affiliated": false,
    "ownership_notes": "Independent outlet"
  }
}
```

**Response 201:**
```json
{
  "id": "uuid",
  "name": "Source Name",
  "created_at": "2025-01-01T10:00:00Z"
}
```

---

## GET /sources/{id}

Get source details.

**Response 200:**
```json
{
  "id": "uuid",
  "name": "Africa Confidential",
  "url": "https://africa-confidential.com",
  "type": "SCRAPER",
  "tier": 2,
  "zones": ["horn_africa", "east_africa", "great_lakes", "sahel", "west_africa_coastal", "southern_africa"],
  "languages": ["en"],
  "reliability_score": 0.95,
  "bias_indicators": {
    "political_lean": "center",
    "state_affiliated": false,
    "ownership_notes": "UK-based specialist publication since 1960"
  },
  "refresh_interval_minutes": 1440,
  "active": true,
  "statistics": {
    "articles_total": 4521,
    "articles_last_30_days": 48,
    "avg_daily_articles": 1.6,
    "times_cited": 892
  },
  "last_fetch_at": "2025-01-01T06:00:00Z",
  "last_fetch_status": "SUCCESS",
  "consecutive_failures": 0,
  "created_at": "2024-01-15T00:00:00Z",
  "updated_at": "2025-01-01T06:00:00Z"
}
```

---

## PUT /sources/{id}

Update source.

**Request Body:**
```json
{
  "name": "Updated Name",
  "tier": 3,
  "active": false
}
```

**Response 200:**
```json
{
  "id": "uuid",
  "updated_at": "2025-01-01T10:00:00Z"
}
```

---

## DELETE /sources/{id}

Delete source (soft delete).

**Response 204:** No content

---

## POST /sources/{id}/test

Test source connectivity and fetch.

**Response 200:**
```json
{
  "status": "SUCCESS",
  "articles_found": 15,
  "sample_headlines": [
    "Article headline 1",
    "Article headline 2"
  ],
  "response_time_ms": 342
}
```

---

# SECTION 3: ARTICLES (INGESTED)

## GET /articles

List ingested articles.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `source_id` | uuid | Filter by source |
| `zone` | string | Filter by detected zone |
| `since` | datetime | Articles after this time |
| `until` | datetime | Articles before this time |
| `processed` | boolean | Filter by processed status |
| `min_relevance` | number | Minimum relevance score |
| `search` | string | Full-text search |
| `page` | integer | Page number |
| `per_page` | integer | Items per page |

**Response 200:**
```json
{
  "data": [
    {
      "id": "uuid",
      "source": {
        "id": "uuid",
        "name": "Financial Times"
      },
      "url": "https://ft.com/content/...",
      "title": "Article title",
      "summary": "Brief summary...",
      "published_at": "2025-01-01T07:30:00Z",
      "zones_detected": [
        {"zone_id": "horn_africa", "confidence": 0.92},
        {"zone_id": "gulf_gcc", "confidence": 0.78}
      ],
      "relevance_score": 0.85,
      "processed": true
    }
  ],
  "pagination": {...}
}
```

---

## GET /articles/{id}

Get full article with extracted entities.

**Response 200:**
```json
{
  "id": "uuid",
  "source": {
    "id": "uuid",
    "name": "Africa Confidential",
    "tier": 2
  },
  "url": "https://...",
  "title": "Ethiopia: Abiy's Somaliland Gambit",
  "content": "Full article text...",
  "published_at": "2025-01-01T00:00:00Z",
  "retrieved_at": "2025-01-01T06:15:00Z",
  "language": "en",
  "zones_detected": [
    {"zone_id": "horn_africa", "confidence": 0.95}
  ],
  "entities_extracted": [
    {
      "text": "Abiy Ahmed",
      "type": "PERSON",
      "normalized_name": "Abiy Ahmed Ali",
      "entity_id": "uuid",
      "confidence": 0.98,
      "start_offset": 45,
      "end_offset": 55
    },
    {
      "text": "Ethiopia",
      "type": "LOCATION",
      "normalized_name": "Federal Democratic Republic of Ethiopia",
      "entity_id": "uuid",
      "confidence": 0.99,
      "start_offset": 12,
      "end_offset": 20
    }
  ],
  "relevance_score": 0.88,
  "embedding_available": true
}
```

---

# SECTION 4: STORY CANDIDATES

## GET /candidates

List story candidates.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | NEW, SCORED, SELECTED, REJECTED |
| `zone` | string | Primary zone |
| `signal_type` | string | BREAKING_EVENT, SLOW_BURN, etc. |
| `min_score` | number | Minimum total score |
| `date` | date | Candidates for specific date |
| `page` | integer | Page number |
| `per_page` | integer | Items per page |

**Response 200:**
```json
{
  "data": [
    {
      "id": "uuid",
      "headline": "Generated headline",
      "summary": "Summary text...",
      "source_count": 4,
      "zone_primary": "horn_africa",
      "zones_secondary": ["gulf_gcc", "egypt"],
      "signal_type": "BREAKING_EVENT",
      "total_score": 7.8,
      "scores": {
        "regional_impact": {"score": 8, "reasoning": "..."},
        "global_systemic_impact": {"score": 6, "reasoning": "..."},
        "novelty": {"score": 9, "reasoning": "..."},
        "analytical_richness": {"score": 9, "reasoning": "..."},
        "interconnection": {"score": 8, "reasoning": "..."},
        "source_quality": {"score": 7, "reasoning": "..."},
        "underreporting": {"score": 7, "reasoning": "..."},
        "audience_relevance": {"score": 8, "reasoning": "..."}
      },
      "status": "SCORED",
      "created_at": "2025-01-01T04:00:00Z"
    }
  ],
  "pagination": {...}
}
```

---

## GET /candidates/{id}

Get candidate details with source articles.

**Response 200:**
```json
{
  "id": "uuid",
  "headline": "Headline",
  "summary": "Summary...",
  "source_articles": [
    {
      "id": "uuid",
      "source_name": "Source Name",
      "title": "Article title",
      "url": "...",
      "published_at": "..."
    }
  ],
  "zone_primary": "horn_africa",
  "zones_secondary": ["gulf_gcc"],
  "signal_type": "BREAKING_EVENT",
  "scores": {...},
  "total_score": 7.8,
  "status": "SCORED",
  "is_followup": false,
  "created_at": "2025-01-01T04:00:00Z"
}
```

---

## POST /candidates/{id}/select

Select candidate for analysis.

**Request Body:**
```json
{
  "edition_id": "uuid",
  "selection_reason": "High novelty, strong regional impact, unique angle"
}
```

**Response 200:**
```json
{
  "story_id": "uuid",
  "status": "QUEUED",
  "message": "Story queued for analysis"
}
```

---

## POST /candidates/{id}/reject

Reject candidate.

**Request Body:**
```json
{
  "rejection_reason": "Insufficient sourcing for claims"
}
```

**Response 200:**
```json
{
  "status": "REJECTED"
}
```

---

# SECTION 5: STORIES (IN ANALYSIS)

## GET /stories

List stories in the pipeline.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `edition_id` | uuid | Filter by edition |
| `status` | string | Pipeline status |
| `zone` | string | Primary zone |
| `page` | integer | Page number |
| `per_page` | integer | Items per page |

**Response 200:**
```json
{
  "data": [
    {
      "id": "uuid",
      "edition_id": "uuid",
      "headline": "Story headline",
      "zone_primary": "horn_africa",
      "status": "PASS2_IN_PROGRESS",
      "current_pass": 2,
      "current_stage": "motivation_analysis",
      "quality_gates_passed": [true, false, false, false],
      "human_review_required": false,
      "total_cost": 1.47,
      "created_at": "2025-01-01T04:30:00Z"
    }
  ],
  "pagination": {...}
}
```

---

## GET /stories/{id}

Get full story with all analysis outputs.

**Response 200:**
```json
{
  "id": "uuid",
  "candidate_id": "uuid",
  "edition_id": "uuid",
  "headline": "Story headline",
  "zone_primary": "horn_africa",
  "zones_secondary": ["gulf_gcc"],
  "status": "PASS3_COMPLETE",
  "current_pass": 3,
  "current_stage": "debate",
  
  "pass1_outputs": {
    "factual_reconstruction": {...},
    "context_analysis": {...},
    "actor_analysis": {...},
    "quality_score": 0.87
  },
  
  "pass2_outputs": {
    "motivation_analysis": {...},
    "chain_analysis": {...},
    "subtlety_analysis": {...},
    "quality_score": 0.82
  },
  
  "pass3_outputs": {
    "theory_analysis": {...},
    "history_analysis": {...},
    "debate_transcript": {...},
    "fact_check_results": {...},
    "verification_results": {...},
    "quality_score": 0.79
  },
  
  "quality_gates_passed": [true, true, true, false],
  
  "flags": [
    {
      "type": "QUALITY_ISSUE",
      "severity": "MEDIUM",
      "message": "Source conflict not fully resolved",
      "created_at": "..."
    }
  ],
  
  "human_review_required": false,
  
  "cost_by_pass": {
    "pass1": 0.45,
    "pass2": 0.67,
    "pass3": 0.89
  },
  "total_cost": 2.01,
  
  "created_at": "2025-01-01T04:30:00Z",
  "updated_at": "2025-01-01T06:15:00Z"
}
```

---

## POST /stories/{id}/retry

Retry failed story from specific pass.

**Request Body:**
```json
{
  "from_pass": 2,
  "reason": "Source data updated"
}
```

**Response 200:**
```json
{
  "status": "QUEUED",
  "message": "Story queued for retry from Pass 2"
}
```

---

## POST /stories/{id}/escalate

Manually escalate for human review.

**Request Body:**
```json
{
  "reason": "Sensitive political content requires editorial review",
  "priority": "HIGH"
}
```

**Response 200:**
```json
{
  "review_id": "uuid",
  "status": "PENDING",
  "assigned_to": null
}
```

---

# SECTION 6: EDITIONS (NEWSLETTERS)

## GET /editions

List editions.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Edition status |
| `from_date` | date | Start date |
| `to_date` | date | End date |
| `page` | integer | Page number |

**Response 200:**
```json
{
  "data": [
    {
      "id": "uuid",
      "date": "2025-01-01",
      "status": "PUBLISHED",
      "stories_count": 5,
      "total_word_count": 28500,
      "total_cost": 8.92,
      "published_at": "2025-01-01T10:00:00Z"
    }
  ],
  "pagination": {...}
}
```

---

## POST /editions

Create new edition.

**Request Body:**
```json
{
  "date": "2025-01-02"
}
```

**Response 201:**
```json
{
  "id": "uuid",
  "date": "2025-01-02",
  "status": "DRAFT",
  "created_at": "2025-01-01T20:00:00Z"
}
```

---

## GET /editions/{id}

Get edition with all content.

**Response 200:**
```json
{
  "id": "uuid",
  "date": "2025-01-01",
  "status": "PUBLISHED",
  
  "preamble": {
    "opening_hook": "...",
    "through_line": "...",
    "what_else_matters": [
      {"headline": "...", "summary": "...", "source_url": "..."}
    ],
    "observation": "..."
  },
  
  "feature_articles": [
    {
      "id": "uuid",
      "headline": "Article 1",
      "subhead": "...",
      "zone_primary": "horn_africa",
      "word_count": 5500,
      "read_time_minutes": 22
    }
  ],
  
  "interstitials": [
    {"position": 2, "headline": "...", "content": "..."}
  ],
  
  "worth_your_time": [
    {"title": "...", "url": "...", "source_name": "...", "description": "..."}
  ],
  
  "close_content": "...",
  
  "total_word_count": 28500,
  "total_cost": 8.92,
  
  "published_at": "2025-01-01T10:00:00Z",
  
  "distribution": {
    "email_sent": true,
    "email_sent_at": "2025-01-01T10:05:00Z",
    "email_recipients": 15420,
    "email_delivered": 15189,
    "email_opened": 8234
  }
}
```

---

## POST /editions/{id}/start-pipeline

Start analysis pipeline for edition.

**Response 200:**
```json
{
  "pipeline_run_id": "uuid",
  "stories_count": 5,
  "estimated_cost": 10.50,
  "estimated_duration_minutes": 45
}
```

---

## POST /editions/{id}/publish

Publish edition.

**Request Body:**
```json
{
  "send_email": true,
  "schedule_at": null  // null for immediate
}
```

**Response 200:**
```json
{
  "status": "PUBLISHED",
  "published_at": "2025-01-01T10:00:00Z",
  "email_scheduled": true
}
```

---

# SECTION 7: PUBLISHED ARTICLES

## GET /articles/published

List published articles.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `zone` | string | Primary zone |
| `theme` | string | Theme tag |
| `actor` | string | Actor mentioned |
| `from_date` | date | Start date |
| `to_date` | date | End date |
| `search` | string | Full-text search |
| `page` | integer | Page number |
| `per_page` | integer | Items per page |

**Response 200:**
```json
{
  "data": [
    {
      "id": "uuid",
      "headline": "Article headline",
      "subhead": "Article subhead",
      "zone_primary": "horn_africa",
      "zones_secondary": ["gulf_gcc"],
      "themes": ["recognition_politics", "regional_security"],
      "word_count": 5500,
      "read_time_minutes": 22,
      "published_at": "2025-01-01T10:00:00Z",
      "confidence_rating": 0.78
    }
  ],
  "pagination": {...}
}
```

---

## GET /articles/published/{id}

Get full published article.

**Response 200:**
```json
{
  "id": "uuid",
  "story_id": "uuid",
  "edition_id": "uuid",
  
  "headline": "Israel Recognizes Somaliland: The Game Behind the Game",
  "subhead": "A recognition that speaks to six capitals at once",
  
  "content": "Full article HTML...",
  "word_count": 5500,
  "read_time_minutes": 22,
  
  "classification": {
    "zone_primary": "horn_africa",
    "zones_secondary": ["gulf_gcc", "levant"],
    "countries": ["IL", "SO", "ET", "AE", "IR"],
    "actors_individual": ["Benjamin Netanyahu", "Muse Bihi Abdi"],
    "actors_institutional": ["Israeli Foreign Ministry", "Somaliland Government"],
    "themes": ["recognition_politics", "regional_security", "red_sea_competition"],
    "concepts_theoretical": ["periphery_doctrine", "norm_erosion"],
    "concepts_strategic": ["red_sea_access", "containment"],
    "historical_parallels": ["Israel-South_Sudan_2011", "Kosovo_independence"]
  },
  
  "story_thread_id": "uuid",
  "previous_coverage": [
    {"id": "uuid", "headline": "Related article 1", "published_at": "..."}
  ],
  
  "predictions": [
    {
      "id": "uuid",
      "prediction_text": "At least one additional country will recognize Somaliland within 12 months",
      "confidence": 0.65,
      "timeframe": "12 months",
      "status": "PENDING"
    }
  ],
  
  "confidence_rating": 0.78,
  
  "sources": [
    {
      "source_id": "uuid",
      "source_name": "Africa Confidential",
      "url": "https://...",
      "accessed_at": "2025-01-01T05:00:00Z"
    }
  ],
  
  "corrections": [],
  
  "costs": {
    "total_cost": 2.34,
    "breakdown": {
      "pass1": 0.45,
      "pass2": 0.67,
      "pass3": 0.89,
      "pass4": 0.33
    }
  },
  
  "published_at": "2025-01-01T10:00:00Z"
}
```

---

## POST /articles/published/{id}/correction

Add correction to article.

**Request Body:**
```json
{
  "original_text": "The text that was wrong",
  "corrected_text": "The corrected text",
  "reason": "Factual error identified",
  "severity": "MODERATE"
}
```

**Response 201:**
```json
{
  "correction_id": "uuid",
  "created_at": "2025-01-01T15:00:00Z"
}
```

---

# SECTION 8: HUMAN REVIEW

## GET /reviews

List human review items.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | PENDING, IN_REVIEW, COMPLETED |
| `severity` | string | LOW, MEDIUM, HIGH, CRITICAL |
| `assigned_to` | uuid | Filter by assignee |
| `page` | integer | Page number |

**Response 200:**
```json
{
  "data": [
    {
      "id": "uuid",
      "story_id": "uuid",
      "story_headline": "Story headline",
      "severity": "HIGH",
      "escalation_triggers": ["confidence_below_threshold", "source_conflict"],
      "status": "PENDING",
      "assigned_to": null,
      "due_at": "2025-01-01T08:00:00Z",
      "created_at": "2025-01-01T05:30:00Z"
    }
  ],
  "pagination": {...}
}
```

---

## GET /reviews/{id}

Get review details with escalation package.

**Response 200:**
```json
{
  "id": "uuid",
  "story_id": "uuid",
  
  "escalation_triggers": ["confidence_below_threshold", "adversarial_unresolved"],
  "severity": "HIGH",
  
  "escalation_package": {
    "article_draft": "Full draft text...",
    "specific_issues": [
      {
        "type": "LOW_CONFIDENCE",
        "severity": "HIGH",
        "description": "Motivation analysis confidence below 0.6",
        "location": "Section 5: Motivation Analysis",
        "suggested_action": "Review alternative hypotheses"
      }
    ],
    "source_documents": ["uuid1", "uuid2"],
    "analysis_chain": {...},
    "debate_transcript": {...},
    "suggested_actions": [
      "Review motivation analysis alternatives",
      "Consider adding confidence hedging"
    ]
  },
  
  "status": "PENDING",
  "assigned_to": null,
  "due_at": "2025-01-01T08:00:00Z",
  "created_at": "2025-01-01T05:30:00Z"
}
```

---

## POST /reviews/{id}/assign

Assign review to user.

**Request Body:**
```json
{
  "user_id": "uuid"
}
```

**Response 200:**
```json
{
  "assigned_to": "uuid",
  "assigned_at": "2025-01-01T06:00:00Z"
}
```

---

## POST /reviews/{id}/resolve

Resolve review.

**Request Body:**
```json
{
  "resolution": "APPROVED_WITH_EDITS",
  "notes": "Added additional hedging to motivation analysis, strengthened sourcing note",
  "edits_made": "Diff or description of edits"
}
```

**Response 200:**
```json
{
  "status": "COMPLETED",
  "resolution": "APPROVED_WITH_EDITS",
  "resolved_at": "2025-01-01T07:30:00Z"
}
```

---

# SECTION 9: PIPELINE OPERATIONS

## GET /pipeline/runs

List pipeline runs.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `edition_id` | uuid | Filter by edition |
| `status` | string | RUNNING, COMPLETED, FAILED |
| `from_date` | datetime | Start time |
| `to_date` | datetime | End time |

**Response 200:**
```json
{
  "data": [
    {
      "id": "uuid",
      "edition_id": "uuid",
      "status": "COMPLETED",
      "started_at": "2025-01-01T04:00:00Z",
      "completed_at": "2025-01-01T05:30:00Z",
      "duration_seconds": 5400,
      "stories_total": 5,
      "stories_completed": 5,
      "cost_total": 8.92,
      "errors_count": 0
    }
  ],
  "pagination": {...}
}
```

---

## GET /pipeline/runs/{id}

Get pipeline run details.

**Response 200:**
```json
{
  "id": "uuid",
  "edition_id": "uuid",
  "status": "COMPLETED",
  
  "started_at": "2025-01-01T04:00:00Z",
  "completed_at": "2025-01-01T05:30:00Z",
  "duration_seconds": 5400,
  
  "stories_total": 5,
  "stories_completed": 5,
  
  "phase_status": {
    "collection": {"status": "COMPLETED", "duration_seconds": 300},
    "analysis": {"status": "COMPLETED", "duration_seconds": 3600},
    "adversarial": {"status": "COMPLETED", "duration_seconds": 900},
    "production": {"status": "COMPLETED", "duration_seconds": 600},
    "assembly": {"status": "COMPLETED", "duration_seconds": 180}
  },
  
  "cost_total": 8.92,
  "cost_by_phase": {
    "collection": 0.12,
    "analysis": 5.45,
    "adversarial": 1.89,
    "production": 1.34,
    "assembly": 0.12
  },
  "cost_by_model": {
    "claude-sonnet-4-20250514": 6.78,
    "gpt-4o-mini": 0.89,
    "claude-3-haiku": 1.25
  },
  
  "errors": []
}
```

---

## POST /pipeline/runs/{id}/pause

Pause running pipeline.

**Response 200:**
```json
{
  "status": "PAUSED",
  "paused_at": "2025-01-01T05:00:00Z"
}
```

---

## POST /pipeline/runs/{id}/resume

Resume paused pipeline.

**Response 200:**
```json
{
  "status": "RUNNING",
  "resumed_at": "2025-01-01T05:15:00Z"
}
```

---

## POST /pipeline/runs/{id}/cancel

Cancel pipeline run.

**Request Body:**
```json
{
  "reason": "Cancellation reason"
}
```

**Response 200:**
```json
{
  "status": "CANCELLED",
  "cancelled_at": "2025-01-01T05:00:00Z"
}
```

---

# SECTION 10: ANALYTICS & COSTS

## GET /analytics/costs

Get cost analytics.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `from_date` | date | Start date |
| `to_date` | date | End date |
| `group_by` | string | day, week, month |

**Response 200:**
```json
{
  "period": {
    "from": "2024-12-01",
    "to": "2024-12-31"
  },
  "summary": {
    "total_cost": 267.45,
    "editions_count": 31,
    "stories_count": 155,
    "avg_cost_per_edition": 8.63,
    "avg_cost_per_story": 1.73
  },
  "by_period": [
    {
      "date": "2024-12-01",
      "cost": 8.92,
      "editions": 1,
      "stories": 5
    }
  ],
  "by_model": {
    "claude-sonnet-4-20250514": 201.34,
    "gpt-4o-mini": 28.56,
    "claude-3-haiku": 37.55
  },
  "by_phase": {
    "collection": 3.72,
    "analysis": 168.91,
    "adversarial": 58.53,
    "production": 41.54,
    "assembly": 3.75
  }
}
```

---

## GET /analytics/quality

Get quality analytics.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `from_date` | date | Start date |
| `to_date` | date | End date |

**Response 200:**
```json
{
  "period": {
    "from": "2024-12-01",
    "to": "2024-12-31"
  },
  "summary": {
    "avg_quality_score": 0.84,
    "pass_rate": 0.92,
    "human_review_rate": 0.18,
    "correction_rate": 0.02
  },
  "by_dimension": {
    "factual_accuracy": 0.91,
    "source_quality": 0.86,
    "analytical_depth": 0.82,
    "logical_coherence": 0.88,
    "uncertainty_calibration": 0.79,
    "voice_consistency": 0.85,
    "completeness": 0.94
  },
  "by_zone": {
    "horn_africa": {"count": 12, "avg_score": 0.86},
    "western_europe": {"count": 8, "avg_score": 0.88}
  },
  "predictions": {
    "total": 89,
    "pending": 67,
    "correct": 15,
    "incorrect": 5,
    "indeterminate": 2,
    "accuracy_rate": 0.75
  }
}
```

---

## GET /analytics/coverage

Get zone coverage analytics.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `from_date` | date | Start date |
| `to_date` | date | End date |

**Response 200:**
```json
{
  "period": {
    "from": "2024-12-01",
    "to": "2024-12-31"
  },
  "by_zone": [
    {
      "zone_id": "horn_africa",
      "zone_name": "Horn of Africa",
      "articles_count": 12,
      "words_total": 66000,
      "avg_article_length": 5500,
      "last_covered": "2024-12-31"
    }
  ],
  "zones_uncovered_7_days": ["mongolia", "caribbean"],
  "zones_uncovered_14_days": [],
  "zone_diversity_score": 0.78
}
```

---

# SECTION 11: ADMINISTRATION

## GET /admin/users

List users.

**Response 200:**
```json
{
  "data": [
    {
      "id": "uuid",
      "email": "editor@theundertow.io",
      "name": "John Smith",
      "role": "EDITOR",
      "status": "ACTIVE",
      "last_login_at": "2025-01-01T08:00:00Z",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

---

## POST /admin/users

Create user.

**Request Body:**
```json
{
  "email": "newuser@theundertow.io",
  "name": "Jane Doe",
  "role": "ANALYST",
  "permissions": ["HUMAN_REVIEW", "SELECT_STORIES"]
}
```

**Response 201:**
```json
{
  "id": "uuid",
  "email": "newuser@theundertow.io",
  "status": "INVITED",
  "invite_link": "https://app.theundertow.io/invite/..."
}
```

---

## GET /admin/config

Get system configuration.

**Response 200:**
```json
{
  "provider": {
    "preference": "ANTHROPIC",
    "openai_available": true,
    "anthropic_available": true
  },
  "budget": {
    "daily_limit": 50.00,
    "daily_spent": 8.92,
    "monthly_limit": 1000.00,
    "monthly_spent": 267.45
  },
  "pipeline": {
    "max_concurrent_stories": 5,
    "timeout_per_story_minutes": 60,
    "retry_attempts": 3
  },
  "quality": {
    "gate1_threshold": 0.75,
    "gate2_threshold": 0.80,
    "gate3_threshold": 0.80,
    "gate4_threshold": 0.85,
    "human_review_threshold": 0.70
  }
}
```

---

## PATCH /admin/config

Update configuration.

**Request Body:**
```json
{
  "budget.daily_limit": 75.00,
  "quality.gate1_threshold": 0.80
}
```

**Response 200:**
```json
{
  "updated": ["budget.daily_limit", "quality.gate1_threshold"],
  "updated_at": "2025-01-01T10:00:00Z"
}
```

---

# ERROR RESPONSES

All endpoints may return these error responses:

## 400 Bad Request
```json
{
  "error": "validation_error",
  "message": "Invalid request body",
  "details": [
    {"field": "email", "error": "Invalid email format"}
  ]
}
```

## 401 Unauthorized
```json
{
  "error": "unauthorized",
  "message": "Invalid or expired token"
}
```

## 403 Forbidden
```json
{
  "error": "forbidden",
  "message": "Insufficient permissions for this action"
}
```

## 404 Not Found
```json
{
  "error": "not_found",
  "message": "Resource not found"
}
```

## 429 Too Many Requests
```json
{
  "error": "rate_limited",
  "message": "Rate limit exceeded",
  "retry_after": 60
}
```

## 500 Internal Server Error
```json
{
  "error": "internal_error",
  "message": "An unexpected error occurred",
  "request_id": "uuid"
}
```

---

# WEBHOOKS

## Webhook Events

Subscribe to events via webhooks:

| Event | Description |
|-------|-------------|
| `edition.published` | Edition published |
| `story.completed` | Story analysis completed |
| `story.failed` | Story analysis failed |
| `review.created` | Human review item created |
| `pipeline.completed` | Pipeline run completed |
| `pipeline.failed` | Pipeline run failed |
| `budget.warning` | Budget threshold reached |

## Webhook Payload

```json
{
  "event": "edition.published",
  "timestamp": "2025-01-01T10:00:00Z",
  "data": {
    "edition_id": "uuid",
    "date": "2025-01-01",
    "stories_count": 5
  }
}
```

---

*API Version: 1.0.0*

