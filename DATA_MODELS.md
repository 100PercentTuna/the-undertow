# The Undertow — Data Models

## Complete Schema Definitions

---

# SECTION 1: CORE ENTITIES

## 1.1 Source

```typescript
interface Source {
  // Primary Key
  id: UUID;
  
  // Basic Info
  name: string;                    // e.g., "Financial Times"
  url: string;                     // Base URL
  type: SourceType;                // RSS | API | SCRAPER
  tier: 1 | 2 | 3 | 4;            // Quality tier
  
  // Coverage
  zones: string[];                 // Zone IDs this source covers
  languages: string[];             // ISO 639-1 codes
  
  // Quality Tracking
  reliability_score: number;       // 0.0-1.0, updated over time
  bias_indicators: {
    political_lean?: 'left' | 'center-left' | 'center' | 'center-right' | 'right';
    state_affiliated: boolean;
    ownership_notes?: string;
  };
  
  // Operational
  refresh_interval_minutes: number;
  active: boolean;
  last_fetch_at?: DateTime;
  last_fetch_status: 'SUCCESS' | 'FAILED' | 'DEGRADED';
  consecutive_failures: number;
  
  // Metadata
  created_at: DateTime;
  updated_at: DateTime;
  created_by: UUID;               // User who added
}

enum SourceType {
  RSS = 'RSS',
  API = 'API',
  SCRAPER = 'SCRAPER'
}

// Tier Definitions:
// Tier 1: Primary sources (government docs, court filings, official statements)
// Tier 2: Quality journalism (wire services, prestige press, investigative outlets)
// Tier 3: Expert analysis (think tanks, academics, specialist newsletters)
// Tier 4: Contextual (state media, partisan outlets, social media)
```

---

## 1.2 Article (Ingested)

```typescript
interface Article {
  // Primary Key
  id: UUID;
  
  // Source Reference
  source_id: UUID;                 // FK to Source
  
  // Content
  url: string;                     // Original article URL (unique)
  title: string;
  content: string;                 // Full text if available
  summary?: string;                // Auto-generated if full text unavailable
  
  // Temporal
  published_at: DateTime;          // When article was published
  retrieved_at: DateTime;          // When we fetched it
  
  // Classification
  language: string;                // Detected language (ISO 639-1)
  zones_detected: ZoneDetection[];
  
  // Extraction
  entities_extracted: ExtractedEntity[];
  
  // Processing
  relevance_score?: number;        // 0.0-1.0
  embedding?: number[];            // Vector embedding
  processed: boolean;
  processed_at?: DateTime;
  
  // Metadata
  created_at: DateTime;
}

interface ZoneDetection {
  zone_id: string;
  confidence: number;              // 0.0-1.0
}

interface ExtractedEntity {
  text: string;                    // As it appears in article
  type: 'PERSON' | 'ORGANIZATION' | 'LOCATION' | 'EVENT';
  normalized_name?: string;        // Canonical form
  entity_id?: UUID;                // FK to Entity if resolved
  confidence: number;
  start_offset: number;
  end_offset: number;
}
```

---

## 1.3 Entity (Knowledge Graph)

```typescript
interface Entity {
  // Primary Key
  id: UUID;
  
  // Identification
  canonical_name: string;          // Primary name
  aliases: string[];               // Alternative names
  type: EntityType;
  
  // Details (type-specific)
  details: PersonDetails | OrganizationDetails | LocationDetails;
  
  // Statistics
  mention_count: number;
  first_seen: DateTime;
  last_seen: DateTime;
  
  // Relationships
  relationships: EntityRelationship[];
  
  // Quality
  verified: boolean;               // Human-verified
  verification_notes?: string;
  
  // Metadata
  created_at: DateTime;
  updated_at: DateTime;
}

enum EntityType {
  PERSON = 'PERSON',
  ORGANIZATION = 'ORGANIZATION',
  LOCATION = 'LOCATION'
}

interface PersonDetails {
  title?: string;                  // Current title/role
  nationality?: string;
  birth_year?: number;
  affiliations: string[];          // Organization names
  biography?: string;
}

interface OrganizationDetails {
  org_type: 'GOVERNMENT' | 'COMPANY' | 'NGO' | 'MILITARY' | 'INTERNATIONAL_ORG' | 'OTHER';
  country?: string;
  parent_org?: string;
  description?: string;
}

interface LocationDetails {
  location_type: 'COUNTRY' | 'CITY' | 'REGION' | 'FACILITY';
  country?: string;
  coordinates?: {
    latitude: number;
    longitude: number;
  };
}

interface EntityRelationship {
  target_entity_id: UUID;
  relationship_type: string;       // e.g., "leader_of", "subsidiary_of", "located_in"
  strength: number;                // 0.0-1.0, based on co-mention frequency
  first_observed: DateTime;
  last_observed: DateTime;
}
```

---

# SECTION 2: STORY PIPELINE

## 2.1 Story Candidate

```typescript
interface StoryCandidate {
  // Primary Key
  id: UUID;
  
  // Content
  headline: string;                // Auto-generated or human-edited
  summary: string;                 // 2-3 sentence summary
  
  // Sources
  source_articles: UUID[];         // FK to Article[]
  source_count: number;
  
  // Classification
  zone_primary: string;
  zones_secondary: string[];
  signal_type: SignalType;
  
  // Scoring (1-10 each)
  scores: StoryScores;
  total_score: number;             // Weighted average
  
  // Status
  status: CandidateStatus;
  
  // Selection
  selected_for_edition?: UUID;     // FK to Edition if selected
  selection_reason?: string;
  
  // Previous Coverage
  is_followup: boolean;
  previous_story_id?: UUID;        // If followup, link to previous
  
  // Metadata
  created_at: DateTime;
  updated_at: DateTime;
  scored_at?: DateTime;
}

enum SignalType {
  BREAKING_EVENT = 'BREAKING_EVENT',
  SLOW_BURN = 'SLOW_BURN',
  WEAK_SIGNAL = 'WEAK_SIGNAL',
  COUNTER_CONSENSUS = 'COUNTER_CONSENSUS',
  STRUCTURAL_SHIFT = 'STRUCTURAL_SHIFT'
}

enum CandidateStatus {
  NEW = 'NEW',
  SCORED = 'SCORED',
  SELECTED = 'SELECTED',
  REJECTED = 'REJECTED',
  ARCHIVED = 'ARCHIVED'
}

interface StoryScores {
  regional_impact: ScoredDimension;
  global_systemic_impact: ScoredDimension;
  novelty: ScoredDimension;
  analytical_richness: ScoredDimension;
  interconnection: ScoredDimension;
  source_quality: ScoredDimension;
  underreporting: ScoredDimension;
  audience_relevance: ScoredDimension;
}

interface ScoredDimension {
  score: number;                   // 1-10
  reasoning: string;
  auto_scored: boolean;
  override_by?: UUID;              // User who overrode if manual
  override_at?: DateTime;
}
```

---

## 2.2 Story (In Analysis)

```typescript
interface Story {
  // Primary Key
  id: UUID;
  
  // Origin
  candidate_id: UUID;              // FK to StoryCandidate
  edition_id: UUID;                // FK to Edition
  
  // Basic Info
  headline: string;
  zone_primary: string;
  zones_secondary: string[];
  
  // Pipeline Status
  status: StoryStatus;
  current_pass: number;            // 1-4
  current_stage: string;           // e.g., "motivation_analysis"
  
  // Pass 1 Outputs
  factual_reconstruction?: FactualReconstruction;
  context_analysis?: ContextAnalysis;
  actor_analysis?: ActorAnalysis;
  pass1_quality_score?: number;
  
  // Pass 2 Outputs
  motivation_analysis?: MotivationAnalysis;
  chain_analysis?: ChainAnalysis;
  subtlety_analysis?: SubtletyAnalysis;
  pass2_quality_score?: number;
  
  // Pass 3 Outputs (Supplementary)
  theory_analysis?: TheoryAnalysis;
  history_analysis?: HistoryAnalysis;
  geometry_analysis?: GeometryAnalysis;
  shockwave_analysis?: ShockwaveAnalysis;
  uncertainty_analysis?: UncertaintyAnalysis;
  
  // Pass 3 Outputs (Adversarial)
  debate_transcript?: DebateTranscript;
  fact_check_results?: FactCheckResults;
  verification_results?: VerificationResults;
  pass3_quality_score?: number;
  
  // Pass 4 Outputs
  article_draft?: string;
  article_final?: string;
  word_count?: number;
  pass4_quality_score?: number;
  
  // Quality & Review
  quality_gates_passed: boolean[];
  human_review_required: boolean;
  human_review_status?: 'PENDING' | 'IN_REVIEW' | 'COMPLETED';
  human_review_by?: UUID;
  human_review_notes?: string;
  
  // Flags
  flags: StoryFlag[];
  
  // Cost Tracking
  cost_by_pass: { [pass: string]: number };
  total_cost: number;
  
  // Metadata
  created_at: DateTime;
  updated_at: DateTime;
  completed_at?: DateTime;
}

enum StoryStatus {
  QUEUED = 'QUEUED',
  PASS1_IN_PROGRESS = 'PASS1_IN_PROGRESS',
  PASS1_COMPLETE = 'PASS1_COMPLETE',
  PASS2_IN_PROGRESS = 'PASS2_IN_PROGRESS',
  PASS2_COMPLETE = 'PASS2_COMPLETE',
  PASS3_IN_PROGRESS = 'PASS3_IN_PROGRESS',
  PASS3_COMPLETE = 'PASS3_COMPLETE',
  PASS4_IN_PROGRESS = 'PASS4_IN_PROGRESS',
  PASS4_COMPLETE = 'PASS4_COMPLETE',
  HUMAN_REVIEW = 'HUMAN_REVIEW',
  READY_FOR_PUBLICATION = 'READY_FOR_PUBLICATION',
  PUBLISHED = 'PUBLISHED',
  FAILED = 'FAILED'
}

interface StoryFlag {
  type: 'QUALITY_ISSUE' | 'HUMAN_REVIEW' | 'MANUAL_EDIT' | 'ESCALATION';
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  message: string;
  created_at: DateTime;
  resolved: boolean;
  resolved_at?: DateTime;
  resolved_by?: UUID;
}
```

---

## 2.3 Analysis Output Types

```typescript
// Pass 1 Types

interface FactualReconstruction {
  timeline: TimelineEvent[];
  key_facts: VerifiedFact[];
  actors: ActorSummary[];
  information_gaps: InformationGap[];
  source_conflicts: SourceConflict[];
  confidence_overall: number;
}

interface TimelineEvent {
  timestamp: DateTime;
  event: string;
  sources: UUID[];
  confidence: 'HIGH' | 'MEDIUM' | 'LOW';
}

interface VerifiedFact {
  statement: string;
  sources: UUID[];
  confidence: 'HIGH' | 'MEDIUM' | 'LOW';
  notes?: string;
}

interface ContextAnalysis {
  immediate_context: ContextLayer;      // Past days/weeks
  recent_context: ContextLayer;         // Past months
  structural_context: ContextLayer;     // Years/decades
  historical_context: ContextLayer;     // Potentially centuries
  assumed_knowledge: string[];          // What reader needs to know
}

interface ContextLayer {
  summary: string;
  key_events: string[];
  relevance: string;
}

interface ActorAnalysis {
  individuals: IndividualActor[];
  institutions: InstitutionalActor[];
  relationships: ActorRelationship[];
}

interface IndividualActor {
  name: string;
  role: string;
  affiliation: string;
  profile: string;
  relevance_to_story: string;
  track_record: string;
}

interface InstitutionalActor {
  name: string;
  type: string;
  role_in_story: string;
  interests: string[];
  constraints: string[];
}

// Pass 2 Types

interface MotivationAnalysis {
  layer1_individual: {
    decision_maker: string;
    political_position: AssessedFactor;
    domestic_needs: AssessedFactor;
    psychology_worldview: AssessedFactor;
    personal_relationships: AssessedFactor;
    legacy: AssessedFactor;
  };
  layer2_institutional: {
    foreign_ministry: AssessedFactor;
    military_intelligence: AssessedFactor;
    economic_actors: AssessedFactor;
    institutional_momentum: AssessedFactor;
  };
  layer3_structural: {
    systemic_position: AssessedFactor;
    threat_environment: AssessedFactor;
    economic_structure: AssessedFactor;
    geographic_imperatives: AssessedFactor;
  };
  layer4_window: {
    what_changed: AssessedFactor;
    position_shifts: AssessedFactor;
    constraint_relaxed: AssessedFactor;
    whats_coming: AssessedFactor;
    convergence: AssessedFactor;
  };
  synthesis: MotivationSynthesis;
}

interface AssessedFactor {
  assessment: string;
  evidence: string;
  confidence: number;              // 0.0-1.0
}

interface MotivationSynthesis {
  primary_driver: {
    layer: 'LAYER_1' | 'LAYER_2' | 'LAYER_3' | 'LAYER_4';
    specific_factor: string;
    explanation: string;
    confidence: number;
  };
  enabling_conditions: string[];
  alternative_hypotheses: AlternativeHypothesis[];
  evidence_that_would_change: string[];
}

interface AlternativeHypothesis {
  hypothesis: string;
  supporting_evidence: string;
  weaknesses: string;
  probability: number;
}

interface ChainAnalysis {
  forward_chains: {
    first_order: ChainEffect[];
    second_order: ChainEffect[];
    third_order: ChainEffect[];
    fourth_order: ChainEffect[];
    fifth_order: ChainEffect[];
  };
  backward_chains: {
    first_order_beneficiaries: Beneficiary[];
    nth_order_beneficiaries: NthOrderBeneficiary[];
  };
  chain_intersections: ChainIntersection[];
}

interface ChainEffect {
  effect: string;
  mechanism: string;
  affected_parties?: string[];
  timeline: string;
  confidence: number;
}

interface Beneficiary {
  beneficiary: string;
  benefit: string;
  means: string;
  intentionality: 'LIKELY_INTENTIONAL' | 'POSSIBLY_INTENTIONAL' | 'LIKELY_COINCIDENTAL';
}

interface NthOrderBeneficiary {
  beneficiary: string;
  order: number;
  benefit: string;
  means: string;
  suspicion_level: 'HIGH' | 'MEDIUM' | 'LOW';
  reasoning: string;
}

interface ChainIntersection {
  this_chain_effect: string;
  intersecting_chain: string;
  interaction: string;
  emergent_outcome: string;
}

// Pass 3 Types (Adversarial)

interface DebateTranscript {
  rounds: DebateRound[];
  judgment: DebateJudgment;
}

interface DebateRound {
  round_number: number;
  advocate_defense: string;
  challenger_challenges: Challenge[];
  advocate_responses: ChallengeResponse[];
}

interface Challenge {
  id: string;
  type: string;
  target: string;
  challenge: string;
  severity: 'CRITICAL' | 'MAJOR' | 'MINOR';
  suggested_fix: string;
}

interface ChallengeResponse {
  challenge_id: string;
  response_type: 'CONCEDE' | 'REBUT' | 'CLARIFY';
  response: string;
  modification_proposed?: string;
}

interface DebateJudgment {
  adjudications: Adjudication[];
  modifications: Modification[];
  confidence_adjustment: {
    original: number;
    adjusted: number;
    reasoning: string;
  };
  unresolved_issues: UnresolvedIssue[];
  verdict: 'ANALYSIS_SOUND' | 'SOUND_WITH_MODIFICATIONS' | 'REQUIRES_MAJOR_REVISION' | 'REJECTED';
}
```

---

# SECTION 3: PUBLICATION

## 3.1 Published Article

```typescript
interface PublishedArticle {
  // Primary Key
  id: UUID;
  
  // Origin
  story_id: UUID;                  // FK to Story
  edition_id: UUID;                // FK to Edition
  
  // Content
  headline: string;
  subhead: string;
  content: string;                 // Full article HTML/Markdown
  word_count: number;
  read_time_minutes: number;
  
  // Classification
  zone_primary: string;
  zones_secondary: string[];
  countries: string[];
  actors_individual: string[];
  actors_institutional: string[];
  themes: string[];
  concepts_theoretical: string[];
  concepts_strategic: string[];
  historical_parallels: string[];
  
  // Linking
  story_thread_id?: UUID;          // For ongoing stories
  previous_coverage: UUID[];       // Links to related past articles
  
  // Predictions
  predictions: ArticlePrediction[];
  
  // Quality
  confidence_rating: number;       // Overall confidence
  
  // Sources
  sources: ArticleSource[];
  
  // Costs
  total_cost: number;
  cost_breakdown: { [stage: string]: number };
  
  // Metadata
  published_at: DateTime;
  events_date?: DateTime;          // When events occurred
  created_at: DateTime;
  updated_at: DateTime;
  
  // Corrections
  corrections: Correction[];
}

interface ArticlePrediction {
  id: UUID;
  prediction_text: string;
  confidence: number;
  timeframe?: string;
  conditions_for_resolution: string;
  status: 'PENDING' | 'CORRECT' | 'INCORRECT' | 'PARTIALLY_CORRECT' | 'INDETERMINATE';
  resolution_notes?: string;
  resolved_at?: DateTime;
  resolved_by?: UUID;
}

interface ArticleSource {
  source_id: UUID;
  source_name: string;
  url: string;
  accessed_at: DateTime;
  citation_context: string;
}

interface Correction {
  id: UUID;
  correction_text: string;
  original_text: string;
  reason: string;
  severity: 'MINOR' | 'MODERATE' | 'MAJOR';
  created_at: DateTime;
  created_by: UUID;
}
```

---

## 3.2 Edition (Newsletter)

```typescript
interface Edition {
  // Primary Key
  id: UUID;
  
  // Timing
  date: Date;                      // Publication date
  
  // Preamble
  preamble: {
    opening_hook: string;
    through_line: string;
    what_else_matters: WhatElseItem[];
    observation: string;
    word_count: number;
  };
  
  // Features
  feature_articles: UUID[];        // FK to PublishedArticle[] (ordered)
  
  // Additional Content
  interstitials: Interstitial[];   // "Meanwhile..." items
  worth_your_time: ExternalLink[];
  corrections: EditionCorrection[];
  
  // Close
  close_content: string;
  
  // Metrics
  total_word_count: number;
  total_cost: number;
  
  // Status
  status: EditionStatus;
  published_at?: DateTime;
  
  // Distribution
  email_sent: boolean;
  email_sent_at?: DateTime;
  email_recipients: number;
  email_delivered: number;
  email_opened: number;
  
  // Metadata
  created_at: DateTime;
  updated_at: DateTime;
  created_by: UUID;
  published_by?: UUID;
}

enum EditionStatus {
  DRAFT = 'DRAFT',
  STORIES_SELECTED = 'STORIES_SELECTED',
  ANALYSIS_IN_PROGRESS = 'ANALYSIS_IN_PROGRESS',
  ARTICLES_COMPLETE = 'ARTICLES_COMPLETE',
  ASSEMBLED = 'ASSEMBLED',
  REVIEW = 'REVIEW',
  APPROVED = 'APPROVED',
  PUBLISHED = 'PUBLISHED'
}

interface WhatElseItem {
  headline: string;
  summary: string;
  source_url: string;
  zone?: string;
}

interface Interstitial {
  position: number;                // After which feature (1-4)
  headline: string;
  content: string;
}

interface ExternalLink {
  title: string;
  url: string;
  source_name: string;
  description: string;
}

interface EditionCorrection {
  article_id: UUID;
  correction_id: UUID;
}
```

---

# SECTION 4: OPERATIONS

## 4.1 Pipeline Run

```typescript
interface PipelineRun {
  // Primary Key
  id: UUID;
  
  // Edition
  edition_id: UUID;
  
  // Timing
  started_at: DateTime;
  completed_at?: DateTime;
  duration_seconds?: number;
  
  // Status
  status: PipelineStatus;
  current_phase: PipelinePhase;
  
  // Progress
  stories_total: number;
  stories_completed: number;
  
  // Phase Details
  phase_status: {
    collection: PhaseStatus;
    analysis: PhaseStatus;
    adversarial: PhaseStatus;
    production: PhaseStatus;
    assembly: PhaseStatus;
  };
  
  // Costs
  cost_total: number;
  cost_by_phase: { [phase: string]: number };
  cost_by_model: { [model: string]: number };
  
  // Errors
  errors: PipelineError[];
  
  // Metadata
  created_at: DateTime;
}

enum PipelineStatus {
  RUNNING = 'RUNNING',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
  PAUSED = 'PAUSED',
  CANCELLED = 'CANCELLED'
}

enum PipelinePhase {
  COLLECTION = 'COLLECTION',
  ANALYSIS = 'ANALYSIS',
  ADVERSARIAL = 'ADVERSARIAL',
  PRODUCTION = 'PRODUCTION',
  ASSEMBLY = 'ASSEMBLY'
}

interface PhaseStatus {
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED';
  started_at?: DateTime;
  completed_at?: DateTime;
  progress_percent: number;
}

interface PipelineError {
  timestamp: DateTime;
  phase: string;
  stage: string;
  story_id?: UUID;
  error_type: string;
  error_message: string;
  stack_trace?: string;
  recovered: boolean;
}
```

---

## 4.2 Cost Log

```typescript
interface CostLog {
  // Primary Key
  id: UUID;
  
  // Context
  story_id?: UUID;
  edition_id?: UUID;
  pipeline_run_id?: UUID;
  
  // Task Info
  agent_name: string;
  task_type: string;
  
  // Model Info
  provider: 'OPENAI' | 'ANTHROPIC';
  model: string;
  tier: 'FRONTIER' | 'HIGH' | 'STANDARD' | 'FAST';
  
  // Usage
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  
  // Cost
  input_cost: number;
  output_cost: number;
  total_cost: number;
  
  // Performance
  latency_ms: number;
  retries: number;
  
  // Metadata
  created_at: DateTime;
}
```

---

## 4.3 Human Review

```typescript
interface HumanReviewItem {
  // Primary Key
  id: UUID;
  
  // What's Being Reviewed
  story_id: UUID;
  
  // Escalation Info
  escalation_triggers: string[];
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  
  // Escalation Package
  escalation_package: {
    article_draft: string;
    specific_issues: ReviewIssue[];
    source_documents: UUID[];
    analysis_chain: object;
    debate_transcript?: object;
    suggested_actions: string[];
  };
  
  // Assignment
  assigned_to?: UUID;
  assigned_at?: DateTime;
  
  // Resolution
  status: 'PENDING' | 'IN_REVIEW' | 'COMPLETED' | 'EXPIRED';
  resolution?: 'APPROVED' | 'APPROVED_WITH_EDITS' | 'REQUEST_REANALYSIS' | 'REJECTED';
  resolution_notes?: string;
  edits_made?: string;
  
  // Timing
  created_at: DateTime;
  due_at: DateTime;
  resolved_at?: DateTime;
  resolved_by?: UUID;
  time_in_review_minutes?: number;
}

interface ReviewIssue {
  type: string;
  severity: string;
  description: string;
  location: string;
  suggested_action: string;
}
```

---

# SECTION 5: USERS & AUTH

## 5.1 User

```typescript
interface User {
  // Primary Key
  id: UUID;
  
  // Identity
  email: string;                   // Unique
  name: string;
  
  // Auth
  password_hash: string;
  password_salt: string;
  mfa_enabled: boolean;
  mfa_secret?: string;
  
  // Role
  role: UserRole;
  permissions: Permission[];       // Additional granular permissions
  
  // Status
  status: 'INVITED' | 'ACTIVE' | 'SUSPENDED' | 'DELETED';
  
  // Activity
  last_login_at?: DateTime;
  login_count: number;
  
  // Preferences
  preferences: {
    timezone: string;
    email_notifications: boolean;
    slack_notifications: boolean;
  };
  
  // Metadata
  created_at: DateTime;
  updated_at: DateTime;
  created_by?: UUID;
}

enum UserRole {
  ADMIN = 'ADMIN',
  EDITOR = 'EDITOR',
  ANALYST = 'ANALYST',
  VIEWER = 'VIEWER'
}

enum Permission {
  // System
  CONFIGURE_SYSTEM = 'CONFIGURE_SYSTEM',
  MANAGE_USERS = 'MANAGE_USERS',
  OVERRIDE_BUDGETS = 'OVERRIDE_BUDGETS',
  
  // Content
  PUBLISH_NEWSLETTER = 'PUBLISH_NEWSLETTER',
  EDIT_ARTICLES = 'EDIT_ARTICLES',
  HUMAN_REVIEW = 'HUMAN_REVIEW',
  SELECT_STORIES = 'SELECT_STORIES',
  
  // Read
  VIEW_DASHBOARD = 'VIEW_DASHBOARD',
  VIEW_ANALYTICS = 'VIEW_ANALYTICS',
  READ_ARTICLES = 'READ_ARTICLES'
}
```

---

## 5.2 Audit Log

```typescript
interface AuditLog {
  // Primary Key
  id: UUID;
  
  // Who
  user_id?: UUID;                  // Null if system action
  user_email?: string;
  
  // What
  action: string;                  // e.g., "USER_LOGIN", "STORY_SELECTED", "ARTICLE_PUBLISHED"
  resource_type: string;           // e.g., "user", "story", "article"
  resource_id?: UUID;
  
  // Details
  details: object;                 // Action-specific details
  
  // Context
  ip_address?: string;
  user_agent?: string;
  
  // When
  created_at: DateTime;
}
```

---

# SECTION 6: CONFIGURATION

## 6.1 System Config

```typescript
interface SystemConfig {
  // Primary Key
  key: string;
  
  // Value
  value: string | number | boolean | object;
  value_type: 'STRING' | 'NUMBER' | 'BOOLEAN' | 'JSON';
  
  // Metadata
  description: string;
  category: string;
  
  // Change Tracking
  updated_at: DateTime;
  updated_by: UUID;
  
  // History
  previous_value?: string;
  previous_updated_at?: DateTime;
}

// Key Categories:
// - provider: AI provider settings
// - budget: Cost limits
// - pipeline: Pipeline configuration
// - quality: Quality thresholds
// - notification: Alert settings
```

---

# DATABASE INDEXES

```sql
-- Articles
CREATE INDEX idx_articles_source ON articles(source_id);
CREATE INDEX idx_articles_published ON articles(published_at);
CREATE INDEX idx_articles_retrieved ON articles(retrieved_at);
CREATE INDEX idx_articles_processed ON articles(processed);

-- Story Candidates
CREATE INDEX idx_candidates_status ON story_candidates(status);
CREATE INDEX idx_candidates_zone ON story_candidates(zone_primary);
CREATE INDEX idx_candidates_score ON story_candidates(total_score DESC);
CREATE INDEX idx_candidates_created ON story_candidates(created_at);

-- Stories
CREATE INDEX idx_stories_edition ON stories(edition_id);
CREATE INDEX idx_stories_status ON stories(status);
CREATE INDEX idx_stories_zone ON stories(zone_primary);

-- Published Articles
CREATE INDEX idx_published_edition ON published_articles(edition_id);
CREATE INDEX idx_published_zone ON published_articles(zone_primary);
CREATE INDEX idx_published_date ON published_articles(published_at);
CREATE INDEX idx_published_thread ON published_articles(story_thread_id);
CREATE INDEX idx_published_themes ON published_articles USING GIN(themes);

-- Editions
CREATE INDEX idx_editions_date ON editions(date);
CREATE INDEX idx_editions_status ON editions(status);

-- Cost Logs
CREATE INDEX idx_costs_story ON cost_logs(story_id);
CREATE INDEX idx_costs_edition ON cost_logs(edition_id);
CREATE INDEX idx_costs_created ON cost_logs(created_at);
CREATE INDEX idx_costs_model ON cost_logs(model);

-- Human Review
CREATE INDEX idx_review_status ON human_review_items(status);
CREATE INDEX idx_review_assigned ON human_review_items(assigned_to);
CREATE INDEX idx_review_due ON human_review_items(due_at);

-- Audit
CREATE INDEX idx_audit_user ON audit_logs(user_id);
CREATE INDEX idx_audit_action ON audit_logs(action);
CREATE INDEX idx_audit_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_created ON audit_logs(created_at);
```

---

*This schema is designed for PostgreSQL with JSONB support. Adjust types as needed for other databases.*

