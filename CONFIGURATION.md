# The Undertow — Configuration Reference

## Complete Configuration Guide

---

# SECTION 1: ENVIRONMENT VARIABLES

## Core Application

```bash
# Application
APP_ENV=production                    # development | staging | production
APP_URL=https://api.theundertow.io
APP_SECRET=<32-character-secret>
LOG_LEVEL=info                        # debug | info | warn | error

# Database
DATABASE_URL=postgresql://user:pass@host:5432/undertow
DATABASE_POOL_SIZE=20
DATABASE_TIMEOUT_MS=30000

# Redis (Caching & Queues)
REDIS_URL=redis://host:6379
REDIS_PASSWORD=<password>

# Vector Database (Embeddings)
PINECONE_API_KEY=<api-key>
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX=undertow-articles
```

---

## AI Provider Configuration

```bash
# Provider Preference
AI_PROVIDER_PREFERENCE=ANTHROPIC      # OPENAI | ANTHROPIC | BEST_FIT

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_ORG_ID=org-...
OPENAI_MAX_RETRIES=3
OPENAI_TIMEOUT_MS=120000

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MAX_RETRIES=3
ANTHROPIC_TIMEOUT_MS=120000

# Model Defaults (can be overridden in config)
DEFAULT_FRONTIER_MODEL=claude-sonnet-4-20250514
DEFAULT_HIGH_MODEL=claude-sonnet-4-20250514
DEFAULT_STANDARD_MODEL=gpt-4o-mini
DEFAULT_FAST_MODEL=claude-3-haiku-20240307
```

---

## External Services

```bash
# Email (SendGrid)
SENDGRID_API_KEY=SG...
SENDGRID_FROM_EMAIL=newsletter@theundertow.io
SENDGRID_FROM_NAME=The Undertow

# Monitoring (Sentry)
SENTRY_DSN=https://...@sentry.io/...

# Analytics
POSTHOG_API_KEY=phc_...
POSTHOG_HOST=https://app.posthog.com

# Slack Notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
SLACK_CHANNEL_ALERTS=#undertow-alerts
SLACK_CHANNEL_REVIEWS=#undertow-reviews
```

---

# SECTION 2: APPLICATION CONFIGURATION

## config/default.yaml

```yaml
# =============================================================================
# THE UNDERTOW - MASTER CONFIGURATION
# =============================================================================

app:
  name: "The Undertow"
  version: "1.0.0"
  timezone: "UTC"
  
# -----------------------------------------------------------------------------
# AI PROVIDER SETTINGS
# -----------------------------------------------------------------------------
ai:
  provider:
    preference: "ANTHROPIC"           # OPENAI | ANTHROPIC | BEST_FIT
    fallback_enabled: true
    fallback_order: ["ANTHROPIC", "OPENAI"]
    
  models:
    # Tier assignments by provider
    openai:
      frontier: "gpt-4o"              # Most capable, highest cost
      high: "gpt-4o"                  # High capability
      standard: "gpt-4o-mini"         # Good capability, lower cost
      fast: "gpt-4o-mini"             # Fast responses, lowest cost
      
    anthropic:
      frontier: "claude-sonnet-4-20250514"
      high: "claude-sonnet-4-20250514"
      standard: "claude-sonnet-4-20250514"
      fast: "claude-3-haiku-20240307"
      
  # Task-to-tier routing
  routing:
    # Collection Phase
    zone_scout: "fast"
    story_scorer: "standard"
    source_aggregator: "fast"
    
    # Analysis Phase - Pass 1
    factual_reconstruction: "standard"
    context_analysis: "standard"
    actor_analysis: "standard"
    
    # Analysis Phase - Pass 2
    motivation_analysis: "frontier"      # Critical analysis
    chain_analysis: "frontier"           # Complex reasoning
    subtlety_analysis: "high"
    
    # Analysis Phase - Pass 3 Supplementary
    theory_analysis: "high"
    history_analysis: "high"
    geometry_analysis: "standard"
    shockwave_analysis: "standard"
    uncertainty_analysis: "standard"
    
    # Analysis Phase - Pass 3 Adversarial
    debate_advocate: "frontier"
    debate_challenger: "frontier"
    debate_judge: "frontier"
    fact_checker: "high"
    source_verifier: "high"
    
    # Production Phase
    article_writer: "frontier"           # Voice quality critical
    voice_calibration: "standard"
    preamble_writer: "high"
    quality_evaluation: "high"
    
    # Pass 4 Critique
    self_critique: "high"
    revision_agent: "high"

  # Complexity escalation rules
  escalation:
    enabled: true
    triggers:
      - condition: "source_conflict_count >= 3"
        upgrade_tiers: 1
      - condition: "zones_affected >= 5"
        upgrade_tiers: 1
      - condition: "actors_count >= 10"
        upgrade_tiers: 1
      - condition: "historical_depth_required"
        upgrade_tiers: 1
        
  # Rate limiting per provider
  rate_limits:
    openai:
      requests_per_minute: 500
      tokens_per_minute: 150000
    anthropic:
      requests_per_minute: 1000
      tokens_per_minute: 200000

# -----------------------------------------------------------------------------
# COST MANAGEMENT
# -----------------------------------------------------------------------------
budget:
  daily_limit: 50.00                    # USD
  monthly_limit: 1000.00                # USD
  
  alerts:
    - threshold: 0.75                   # 75% of daily limit
      channel: "slack"
      message: "Daily budget 75% consumed"
    - threshold: 0.90                   # 90% of daily limit
      channel: "slack"
      priority: "high"
      message: "Daily budget 90% consumed - approaching limit"
    - threshold: 1.00                   # 100% of daily limit
      channel: "slack"
      priority: "critical"
      message: "Daily budget exhausted - pipeline paused"
      action: "pause_pipeline"
      
  cost_per_1k_tokens:
    openai:
      gpt-4o:
        input: 0.0025
        output: 0.01
      gpt-4o-mini:
        input: 0.00015
        output: 0.0006
    anthropic:
      claude-sonnet-4-20250514:
        input: 0.003
        output: 0.015
      claude-3-haiku-20240307:
        input: 0.00025
        output: 0.00125

# -----------------------------------------------------------------------------
# PIPELINE CONFIGURATION
# -----------------------------------------------------------------------------
pipeline:
  # Story selection
  stories_per_edition: 5
  min_candidate_score: 5.5
  
  # Execution settings
  max_concurrent_stories: 5
  timeout_per_story_minutes: 60
  retry_attempts: 3
  retry_backoff_seconds: [10, 30, 60]
  
  # Pass configuration
  passes:
    pass1:
      name: "Foundation"
      stages:
        - factual_reconstruction
        - context_analysis
        - actor_analysis
      quality_gate_threshold: 0.75
      max_iterations: 2
      
    pass2:
      name: "Core Analysis"
      stages:
        - motivation_analysis
        - chain_analysis
        - subtlety_analysis
      quality_gate_threshold: 0.80
      max_iterations: 3
      
    pass3:
      name: "Enhancement & Verification"
      parallel_groups:
        supplementary:
          - theory_analysis
          - history_analysis
          - geometry_analysis
          - shockwave_analysis
          - uncertainty_analysis
        adversarial:
          - debate                      # 3-round debate
          - fact_check
          - source_verification
      quality_gate_threshold: 0.80
      debate_rounds: 3
      
    pass4:
      name: "Production"
      stages:
        - article_writing
        - voice_calibration
        - quality_evaluation
      critique_revision_cycles: 2
      quality_gate_threshold: 0.85
      
  # Early termination
  early_termination:
    enabled: true
    conditions:
      - "quality_score >= 0.95 after pass2"
      - "no_issues_found in adversarial"
      
  # Scheduling
  schedule:
    collection_start: "00:00"           # UTC
    analysis_start: "04:00"             # UTC
    target_publish: "10:00"             # UTC
    timezone: "UTC"

# -----------------------------------------------------------------------------
# QUALITY STANDARDS
# -----------------------------------------------------------------------------
quality:
  # Gate thresholds
  gates:
    foundation:
      threshold: 0.75
      required_components:
        - timeline_complete
        - key_facts_sourced
        - actors_identified
        
    analysis:
      threshold: 0.80
      required_components:
        - motivation_4_layers
        - chains_4_orders
        - alternatives_generated
        
    adversarial:
      threshold: 0.80
      required_components:
        - debate_completed
        - facts_verified
        - sources_cross_checked
        
    output:
      threshold: 0.85
      required_components:
        - voice_consistent
        - structure_complete
        - sources_cited
        
  # Dimension weights for quality scoring
  dimension_weights:
    factual_accuracy: 0.20
    source_quality: 0.15
    analytical_depth: 0.20
    logical_coherence: 0.15
    uncertainty_calibration: 0.10
    voice_consistency: 0.10
    completeness: 0.10
    
  # Source requirements
  sourcing:
    min_sources_per_major_claim: 2
    preferred_tier_for_facts: [1, 2]
    acceptable_tier_for_context: [1, 2, 3]
    max_single_source_reliance: 0.40   # No single source > 40% of citations

# -----------------------------------------------------------------------------
# HUMAN REVIEW SYSTEM
# -----------------------------------------------------------------------------
human_review:
  enabled: true
  
  # Automatic escalation triggers
  triggers:
    - condition: "overall_confidence < 0.70"
      severity: "HIGH"
    - condition: "verification_score < 0.75"
      severity: "HIGH"
    - condition: "adversarial_unresolved_critical > 0"
      severity: "HIGH"
    - condition: "zones_affected >= 5 AND novelty_score >= 8"
      severity: "MEDIUM"
    - condition: "signal_type == 'COUNTER_CONSENSUS'"
      severity: "MEDIUM"
    - condition: "mentions_heads_of_state >= 3"
      severity: "MEDIUM"
    - condition: "topic IN ['nuclear', 'war', 'terrorism']"
      severity: "HIGH"
      
  # Assignment
  assignment:
    auto_assign: true
    assignment_strategy: "round_robin"   # round_robin | load_balanced | expertise_matched
    max_reviews_per_user: 3
    
  # Timing
  timing:
    response_target_minutes: 30
    escalation_after_minutes: 60
    final_deadline_minutes: 120
    
  # Notifications
  notifications:
    new_review:
      channels: ["email", "slack"]
    approaching_deadline:
      channels: ["slack"]
      threshold_minutes: 15
    deadline_missed:
      channels: ["slack", "email"]
      priority: "high"

# -----------------------------------------------------------------------------
# CACHING CONFIGURATION
# -----------------------------------------------------------------------------
cache:
  enabled: true
  
  # Embedding cache
  embeddings:
    enabled: true
    ttl_days: 30
    max_size_gb: 10
    
  # RAG cache
  rag:
    enabled: true
    query_cache_ttl_hours: 24
    document_cache_ttl_hours: 168       # 7 days
    
  # LLM response cache
  llm_responses:
    enabled: true
    cache_identical_prompts: true
    ttl_hours: 24
    
  # Analysis cache (for incremental updates)
  analysis:
    enabled: true
    reuse_pass1_if_sources_unchanged: true
    ttl_hours: 48

# -----------------------------------------------------------------------------
# RAG CONFIGURATION
# -----------------------------------------------------------------------------
rag:
  # Query processing
  query:
    expansion_enabled: true
    expansion_count: 3
    hyde_enabled: true                  # Hypothetical Document Embedding
    
  # Retrieval
  retrieval:
    strategy: "hybrid"                  # dense | sparse | hybrid
    dense_weight: 0.6
    sparse_weight: 0.4
    initial_candidates: 50
    
  # Reranking
  reranking:
    enabled: true
    model: "cross-encoder"
    top_k_after_rerank: 15
    
  # Diversity
  diversity:
    mmr_enabled: true                   # Maximal Marginal Relevance
    lambda: 0.7                         # 0=diversity, 1=relevance
    
  # Source filtering
  source_filter:
    min_tier: 4                         # Include all tiers
    recency_boost: true
    recency_half_life_days: 7

# -----------------------------------------------------------------------------
# SOURCE CONFIGURATION
# -----------------------------------------------------------------------------
sources:
  # Refresh intervals by tier
  refresh_intervals:
    tier1: 60                           # Primary sources: 1 hour
    tier2: 120                          # Quality journalism: 2 hours
    tier3: 360                          # Expert analysis: 6 hours
    tier4: 720                          # Contextual: 12 hours
    
  # Health monitoring
  health:
    consecutive_failures_before_disable: 5
    auto_reenable_after_hours: 24
    alert_on_failures: 3
    
  # Content extraction
  extraction:
    max_article_length: 50000           # Characters
    language_detection: true
    entity_extraction: true
    embedding_generation: true

# -----------------------------------------------------------------------------
# NOTIFICATION CONFIGURATION
# -----------------------------------------------------------------------------
notifications:
  slack:
    enabled: true
    channels:
      alerts: "#undertow-alerts"
      reviews: "#undertow-reviews"
      daily_summary: "#undertow-summary"
      
  email:
    enabled: true
    daily_digest: true
    digest_time: "09:00"                # UTC
    
  events:
    pipeline_complete:
      slack: true
      email: false
    pipeline_failed:
      slack: true
      email: true
      priority: "high"
    human_review_needed:
      slack: true
      email: true
    budget_warning:
      slack: true
      email: true
    edition_published:
      slack: true
      email: false

# -----------------------------------------------------------------------------
# ZONES CONFIGURATION
# -----------------------------------------------------------------------------
zones:
  # Zone definitions with metadata
  definitions:
    - id: "western_europe"
      name: "Western Europe"
      region: "EUROPE"
      countries: ["FR", "DE", "NL", "BE", "LU", "AT", "CH"]
      
    - id: "southern_europe"
      name: "Southern Europe"
      region: "EUROPE"
      countries: ["IT", "ES", "PT", "GR", "CY", "MT"]
      
    # ... (all 42 zones)
    
  # Coverage requirements
  coverage:
    min_coverage_frequency_days: 14     # No zone uncovered > 14 days
    diversity_target: 0.70              # At least 70% zone diversity monthly
    
    # Regional balance targets
    regional_balance:
      EUROPE: 0.20
      MIDDLE_EAST: 0.15
      AFRICA: 0.20
      ASIA: 0.20
      AMERICAS: 0.15
      OCEANIA: 0.10

# -----------------------------------------------------------------------------
# CONTROLLED VOCABULARIES
# -----------------------------------------------------------------------------
vocabularies:
  themes:
    - "alliance_dynamics"
    - "arms_trade"
    - "border_disputes"
    - "civil_conflict"
    - "climate_security"
    - "corruption"
    - "cyber_operations"
    - "debt_diplomacy"
    - "democratic_backsliding"
    - "diaspora_politics"
    - "economic_statecraft"
    - "election_interference"
    - "energy_security"
    - "ethnic_conflict"
    - "financial_flows"
    - "food_security"
    - "great_power_competition"
    - "humanitarian_crisis"
    - "intelligence_operations"
    - "leadership_succession"
    - "maritime_security"
    - "migration"
    - "military_modernization"
    - "nuclear_proliferation"
    - "peacekeeping"
    - "proxy_warfare"
    - "recognition_politics"
    - "regional_integration"
    - "religious_politics"
    - "sanctions"
    - "separatism"
    - "supply_chain_security"
    - "terrorism"
    - "trade_disputes"
    - "treaty_negotiations"
    - "water_politics"
    
  theoretical_concepts:
    - "balance_of_power"
    - "bandwagoning"
    - "buffer_state"
    - "containment"
    - "credible_commitment"
    - "deterrence"
    - "domino_theory"
    - "extended_deterrence"
    - "hedging"
    - "hegemonic_stability"
    - "liberal_institutionalism"
    - "multi_polarity"
    - "offshore_balancing"
    - "periphery_doctrine"
    - "power_transition"
    - "realism"
    - "resource_curse"
    - "security_dilemma"
    - "soft_power"
    - "spheres_of_influence"
    - "strategic_autonomy"
    - "thucydides_trap"
    
  strategic_concepts:
    - "access_denial"
    - "area_denial"
    - "asymmetric_warfare"
    - "basing_rights"
    - "chokepoint_control"
    - "coalition_building"
    - "coercive_diplomacy"
    - "compellence"
    - "counterinsurgency"
    - "economic_leverage"
    - "escalation_dominance"
    - "forward_presence"
    - "gray_zone_operations"
    - "hybrid_warfare"
    - "intelligence_sharing"
    - "interoperability"
    - "power_projection"
    - "sea_lane_security"
    - "signaling"
    - "strategic_patience"
    - "tripwire_forces"

# -----------------------------------------------------------------------------
# ARTICLE STRUCTURE
# -----------------------------------------------------------------------------
article:
  sections:
    - id: "hook"
      name: "The Hook"
      word_range: [300, 500]
      required: true
      
    - id: "what_happened"
      name: "What Happened"
      word_range: [600, 1000]
      required: true
      
    - id: "actors"
      name: "The Actors"
      word_range: [500, 800]
      required: true
      
    - id: "backstory"
      name: "The Backstory"
      word_range: [600, 900]
      required: true
      
    - id: "motivation"
      name: "The Motivation Analysis"
      word_range: [800, 1200]
      required: true
      
    - id: "subtleties"
      name: "The Subtleties"
      word_range: [600, 900]
      required: true
      
    - id: "chains"
      name: "The Chains"
      word_range: [1000, 1500]
      required: true
      
    - id: "geometry"
      name: "The Geometry"
      word_range: [400, 600]
      required: true
      
    - id: "theory_history"
      name: "Theory & History"
      word_range: [600, 1000]
      required: true
      
    - id: "shockwaves"
      name: "The Shockwaves"
      word_range: [500, 700]
      required: true
      
    - id: "unknowns"
      name: "What We Don't Know"
      word_range: [300, 500]
      required: true
      
    - id: "takeaway"
      name: "The Takeaway"
      word_range: [300, 400]
      required: true
      
  total_word_range: [5000, 8000]

# -----------------------------------------------------------------------------
# LOGGING CONFIGURATION
# -----------------------------------------------------------------------------
logging:
  level: "info"
  format: "json"
  
  # Per-component levels
  components:
    pipeline: "info"
    ai: "info"
    database: "warn"
    cache: "warn"
    http: "info"
    
  # Audit logging
  audit:
    enabled: true
    events:
      - "user.login"
      - "user.logout"
      - "story.selected"
      - "story.published"
      - "config.changed"
      - "budget.exceeded"
      
  # Performance logging
  performance:
    enabled: true
    slow_query_threshold_ms: 1000
    slow_api_threshold_ms: 5000
```

---

# SECTION 3: ENVIRONMENT-SPECIFIC OVERRIDES

## config/production.yaml

```yaml
# Production-specific overrides

app:
  debug: false
  
ai:
  rate_limits:
    openai:
      requests_per_minute: 1000
      tokens_per_minute: 300000
    anthropic:
      requests_per_minute: 2000
      tokens_per_minute: 400000
      
budget:
  daily_limit: 100.00
  monthly_limit: 2000.00
  
pipeline:
  max_concurrent_stories: 10
  
cache:
  embeddings:
    max_size_gb: 50
    
logging:
  level: "warn"
```

---

## config/development.yaml

```yaml
# Development-specific overrides

app:
  debug: true
  
budget:
  daily_limit: 10.00
  monthly_limit: 100.00
  
pipeline:
  stories_per_edition: 2
  max_concurrent_stories: 2
  
quality:
  gates:
    foundation:
      threshold: 0.60
    analysis:
      threshold: 0.65
    adversarial:
      threshold: 0.65
    output:
      threshold: 0.70
      
logging:
  level: "debug"
```

---

# SECTION 4: DOCKER CONFIGURATION

## docker-compose.yml

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "3000:3000"
    environment:
      - APP_ENV=production
      - DATABASE_URL=postgresql://user:pass@db:5432/undertow
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    restart: always
    
  worker:
    build: .
    command: npm run worker
    environment:
      - APP_ENV=production
      - DATABASE_URL=postgresql://user:pass@db:5432/undertow
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    restart: always
    deploy:
      replicas: 3
      
  scheduler:
    build: .
    command: npm run scheduler
    environment:
      - APP_ENV=production
      - DATABASE_URL=postgresql://user:pass@db:5432/undertow
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    restart: always
    
  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=undertow
    restart: always
    
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: always

volumes:
  postgres_data:
  redis_data:
```

---

# SECTION 5: INFRASTRUCTURE AS CODE

## terraform/main.tf (AWS Example)

```hcl
# AWS Infrastructure for The Undertow

provider "aws" {
  region = var.aws_region
}

# VPC
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  
  name = "undertow-vpc"
  cidr = "10.0.0.0/16"
  
  azs             = ["${var.aws_region}a", "${var.aws_region}b"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24"]
  
  enable_nat_gateway = true
  single_nat_gateway = true
}

# RDS PostgreSQL
resource "aws_db_instance" "main" {
  identifier        = "undertow-db"
  engine            = "postgres"
  engine_version    = "15"
  instance_class    = "db.r6g.large"
  allocated_storage = 100
  
  db_name  = "undertow"
  username = var.db_username
  password = var.db_password
  
  vpc_security_group_ids = [aws_security_group.db.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  
  backup_retention_period = 7
  multi_az               = true
  
  skip_final_snapshot = false
  final_snapshot_identifier = "undertow-final-snapshot"
}

# ElastiCache Redis
resource "aws_elasticache_cluster" "main" {
  cluster_id           = "undertow-redis"
  engine               = "redis"
  node_type            = "cache.r6g.large"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  port                 = 6379
  
  subnet_group_name    = aws_elasticache_subnet_group.main.name
  security_group_ids   = [aws_security_group.redis.id]
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "undertow-cluster"
  
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "undertow-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = module.vpc.public_subnets
}

# S3 for article storage
resource "aws_s3_bucket" "articles" {
  bucket = "undertow-articles-${var.environment}"
}

resource "aws_s3_bucket_versioning" "articles" {
  bucket = aws_s3_bucket.articles.id
  versioning_configuration {
    status = "Enabled"
  }
}
```

---

# SECTION 6: MONITORING CONFIGURATION

## prometheus/alerts.yml

```yaml
groups:
  - name: undertow_alerts
    rules:
      # Budget alerts
      - alert: BudgetWarning
        expr: undertow_daily_cost / undertow_daily_budget > 0.8
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Daily budget 80% consumed"
          
      - alert: BudgetCritical
        expr: undertow_daily_cost / undertow_daily_budget > 0.95
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Daily budget nearly exhausted"
          
      # Pipeline health
      - alert: PipelineFailed
        expr: undertow_pipeline_status == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Pipeline run failed"
          
      - alert: PipelineSlow
        expr: undertow_pipeline_duration_seconds > 7200
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Pipeline taking longer than expected"
          
      # Quality alerts
      - alert: QualityDegraded
        expr: avg(undertow_article_quality_score) < 0.75
        for: 30m
        labels:
          severity: warning
        annotations:
          summary: "Article quality scores degraded"
          
      # AI provider health
      - alert: AIProviderErrors
        expr: rate(undertow_ai_errors_total[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High AI provider error rate"
          
      # Source health
      - alert: SourcesFailing
        expr: count(undertow_source_status == 0) > 10
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "Multiple sources failing"
```

---

*Configuration Version: 1.0.0*

