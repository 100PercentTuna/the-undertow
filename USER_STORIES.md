# The Undertow — User Stories

## Document Version: 1.0
## Last Updated: January 2026

---

# EPIC 1: SYSTEM CONFIGURATION & PROVIDER MANAGEMENT

## US-1.1: Configure AI Provider Preference

**As a** system administrator  
**I want to** configure which AI provider (OpenAI, Anthropic, or Best-Fit) the system uses  
**So that** I can control costs, comply with organizational policies, or optimize for specific capabilities

### Acceptance Criteria

1. **GIVEN** I am on the System Configuration page  
   **WHEN** I view the Provider Settings section  
   **THEN** I see three options: "OpenAI Only", "Anthropic Only", "Best-Fit (Automatic)"

2. **GIVEN** I select "OpenAI Only"  
   **WHEN** I save the configuration  
   **THEN** all subsequent API calls use only OpenAI models (o1, gpt-4o, gpt-4o-mini)  
   **AND** the system displays a confirmation message "Provider set to OpenAI Only"  
   **AND** the change takes effect within 60 seconds for new tasks

3. **GIVEN** I select "Anthropic Only"  
   **WHEN** I save the configuration  
   **THEN** all subsequent API calls use only Anthropic models (claude-sonnet-4, claude-3-5-sonnet, claude-3-5-haiku)  
   **AND** the system displays a confirmation message "Provider set to Anthropic Only"

4. **GIVEN** I select "Best-Fit (Automatic)"  
   **WHEN** I save the configuration  
   **THEN** the system automatically selects the optimal provider per task type based on the routing rules:
   - Chain mapping, motivation analysis, long-form writing → Anthropic
   - Structured extraction, classification, JSON generation → OpenAI
   - All other tasks → Default provider (configurable)

5. **GIVEN** I have set a provider preference  
   **WHEN** that provider experiences an outage or rate limit  
   **THEN** the system automatically falls back to the alternative provider  
   **AND** logs the fallback event with timestamp, original provider, fallback provider, and task type  
   **AND** displays an alert on the dashboard

### Technical Notes
- Provider configuration stored in `system_config` table with key `ai_provider_preference`
- Changes should not interrupt in-flight tasks
- Fallback behavior must be configurable (enabled/disabled)

### Priority: P0 (Must Have)
### Story Points: 5
### Dependencies: None

---

## US-1.2: Configure Model Tier Overrides

**As a** system administrator  
**I want to** override the default model tier for specific task types  
**So that** I can optimize quality/cost tradeoffs for my specific use case

### Acceptance Criteria

1. **GIVEN** I am on the Model Configuration page  
   **WHEN** I view the Task-to-Tier mapping table  
   **THEN** I see all 30+ task types with their current tier assignment:
   | Task Type | Default Tier | Current Override | Estimated Cost Impact |
   |-----------|--------------|------------------|----------------------|
   | motivation_analysis | FRONTIER | (none) | Baseline |
   | factual_reconstruction | HIGH | (none) | Baseline |
   | ... | ... | ... | ... |

2. **GIVEN** I click "Override" for the task "factual_reconstruction"  
   **WHEN** I select "FRONTIER" from the tier dropdown  
   **AND** I click "Save Override"  
   **THEN** the system displays the estimated cost impact (e.g., "+$0.45 per article")  
   **AND** requires confirmation before saving  
   **AND** updates the task routing immediately for new tasks

3. **GIVEN** I have set an override for a task  
   **WHEN** I click "Reset to Default"  
   **THEN** the override is removed  
   **AND** the task uses the system default tier

4. **GIVEN** I am viewing the override configuration  
   **WHEN** I click "Export Configuration"  
   **THEN** the system downloads a JSON file with all current tier assignments  
   **AND** the file can be imported on another instance

5. **GIVEN** I upload a configuration JSON file  
   **WHEN** the file format is valid  
   **THEN** the system previews all changes before applying  
   **AND** highlights any differences from current configuration  
   **AND** requires confirmation to apply

### Validation Rules
- Tier must be one of: FRONTIER, HIGH, STANDARD, FAST
- Task type must be a valid registered task type
- Cost impact calculation based on average token usage for task type

### Priority: P1 (Should Have)
### Story Points: 8
### Dependencies: US-1.1

---

## US-1.3: Set API Keys and Credentials

**As a** system administrator  
**I want to** securely configure API keys for OpenAI and Anthropic  
**So that** the system can authenticate with the AI providers

### Acceptance Criteria

1. **GIVEN** I am on the API Credentials page  
   **WHEN** I view the OpenAI section  
   **THEN** I see:
   - A masked input field showing "sk-****...****" if a key is set, or "Not configured" if not
   - A "Test Connection" button
   - A "Rotate Key" button (if key exists)
   - Last successful API call timestamp

2. **GIVEN** I enter a new OpenAI API key  
   **WHEN** I click "Save"  
   **THEN** the system validates the key format (starts with "sk-", correct length)  
   **AND** makes a test API call to verify the key works  
   **AND** displays "Key validated successfully" or specific error message  
   **AND** stores the key encrypted using AES-256 in the secrets store

3. **GIVEN** I click "Test Connection" for a configured provider  
   **WHEN** the connection succeeds  
   **THEN** the system displays:
   - "Connection successful"
   - Current rate limit status (requests remaining, reset time)
   - Account tier/organization name
   **WHEN** the connection fails  
   **THEN** the system displays specific error (invalid key, expired, rate limited, network error)

4. **GIVEN** I click "Rotate Key"  
   **WHEN** I enter a new key  
   **THEN** the system validates the new key before replacing the old one  
   **AND** the old key is immediately invalidated in the system  
   **AND** the change is logged in the audit log

5. **GIVEN** an API key is not configured for a provider  
   **WHEN** the system attempts to use that provider  
   **THEN** the task fails with a clear error "API key not configured for [provider]"  
   **AND** falls back to alternative provider if configured  
   **AND** sends an alert to administrators

### Security Requirements
- API keys must never be logged in plaintext
- API keys must be stored encrypted at rest
- API keys must be transmitted only over HTTPS
- API key access must be audited

### Priority: P0 (Must Have)
### Story Points: 5
### Dependencies: None

---

## US-1.4: Configure Cost Budgets and Alerts

**As a** system administrator  
**I want to** set daily and monthly cost budgets with alerts  
**So that** I can prevent unexpected cost overruns

### Acceptance Criteria

1. **GIVEN** I am on the Budget Configuration page  
   **WHEN** I view the budget settings  
   **THEN** I see input fields for:
   - Daily soft limit (warning threshold)
   - Daily hard limit (stop threshold)
   - Monthly soft limit (warning threshold)
   - Monthly hard limit (stop threshold)

2. **GIVEN** I set a daily soft limit of $80  
   **WHEN** the daily spend reaches $80  
   **THEN** the system sends an alert via configured channels (email, Slack)  
   **AND** continues processing normally  
   **AND** the dashboard shows a yellow warning indicator

3. **GIVEN** I set a daily hard limit of $150  
   **WHEN** the daily spend reaches $150  
   **THEN** the system sends a critical alert via all configured channels  
   **AND** pauses all non-critical processing  
   **AND** continues only tasks marked as "critical path"  
   **AND** the dashboard shows a red critical indicator  
   **AND** requires administrator action to resume normal processing

4. **GIVEN** the hard limit has been reached  
   **WHEN** I click "Override Hard Limit"  
   **AND** I enter a reason and new temporary limit  
   **THEN** the system logs the override with administrator identity, reason, and new limit  
   **AND** resumes processing up to the new limit  
   **AND** the override expires at end of day (midnight UTC)

5. **GIVEN** I configure alert channels  
   **WHEN** I add an email address or Slack webhook  
   **THEN** the system sends a test alert to verify the channel works  
   **AND** I can configure which alert types go to which channels

### Budget Calculation Rules
- Costs calculated in real-time based on token usage × provider pricing
- Includes: input tokens, output tokens, embedding calls
- Does not include: infrastructure costs, storage costs

### Priority: P0 (Must Have)
### Story Points: 8
### Dependencies: US-1.3

---

# EPIC 2: SOURCE INGESTION & KNOWLEDGE MANAGEMENT

## US-2.1: Configure Source Feeds

**As a** content administrator  
**I want to** configure RSS feeds and news API sources for each zone  
**So that** the system can automatically collect relevant news

### Acceptance Criteria

1. **GIVEN** I am on the Source Management page  
   **WHEN** I click "Add New Source"  
   **THEN** I see a form with fields:
   - Source Name (required, text, max 200 chars)
   - Source URL (required, valid URL format)
   - Source Type (dropdown: RSS, REST API, Web Scraper)
   - Tier (dropdown: 1-Primary, 2-Quality Journalism, 3-Expert Analysis, 4-Contextual)
   - Zones (multi-select from 42 zones)
   - Languages (multi-select)
   - Refresh Interval (dropdown: 15min, 30min, 1hr, 4hr, 12hr, 24hr)
   - Active (toggle, default: true)

2. **GIVEN** I enter source details and click "Test Source"  
   **WHEN** the source is reachable and parseable  
   **THEN** the system displays:
   - "Source accessible"
   - Number of articles found
   - Sample of 3 recent article titles
   - Detected language
   **WHEN** the source is not reachable or parseable  
   **THEN** the system displays specific error (DNS failure, 404, parse error, rate limited)

3. **GIVEN** I save a new source  
   **WHEN** the source is saved successfully  
   **THEN** the system immediately performs first fetch  
   **AND** schedules recurring fetches at the configured interval  
   **AND** the source appears in the source list with status "Active"

4. **GIVEN** I am viewing the source list  
   **WHEN** I filter by zone "Horn of Africa"  
   **THEN** I see only sources configured for that zone  
   **AND** I can see: source name, tier, last fetch time, articles fetched (24h), error count (24h)

5. **GIVEN** a source has failed 5 consecutive fetches  
   **WHEN** the 5th failure occurs  
   **THEN** the system marks the source as "Degraded"  
   **AND** sends an alert to administrators  
   **AND** continues attempting fetches but at reduced frequency (2x interval)

### Data Model
```
Source {
  id: UUID
  name: string
  url: string
  type: enum(RSS, API, SCRAPER)
  tier: integer(1-4)
  zones: string[]
  languages: string[]
  refresh_interval_minutes: integer
  active: boolean
  created_at: timestamp
  last_fetch_at: timestamp
  last_fetch_status: enum(SUCCESS, FAILED, DEGRADED)
  consecutive_failures: integer
}
```

### Priority: P0 (Must Have)
### Story Points: 13
### Dependencies: None

---

## US-2.2: View and Search Ingested Articles

**As an** analyst  
**I want to** search and browse articles that have been ingested  
**So that** I can verify the system is capturing relevant news and find specific content

### Acceptance Criteria

1. **GIVEN** I am on the Article Browser page  
   **WHEN** I view the default state  
   **THEN** I see articles from the last 24 hours, sorted by ingestion time (newest first)  
   **AND** each article shows: title, source name, source tier badge, publication time, detected zones, relevance score

2. **GIVEN** I enter a search query "Ethiopia port access"  
   **WHEN** I click Search  
   **THEN** the system performs semantic search across article titles and content  
   **AND** returns results ranked by relevance  
   **AND** highlights matching terms in the results  
   **AND** shows relevance score for each result

3. **GIVEN** I apply filters  
   **WHEN** I select:
   - Zone: "Horn of Africa"
   - Source Tier: "1" and "2"
   - Date Range: "Last 7 days"
   - Language: "English"
   **THEN** the results are filtered to match ALL criteria (AND logic)  
   **AND** the filter state is reflected in the URL (bookmarkable)

4. **GIVEN** I click on an article  
   **WHEN** the article detail modal opens  
   **THEN** I see:
   - Full article title
   - Source name with link to source configuration
   - Publication date and ingestion date
   - Full article content (if available) or summary
   - Extracted entities (people, organizations, locations)
   - Detected zones with confidence scores
   - Similar articles (based on embedding similarity)
   - "Flag for Review" button
   - "Mark as Duplicate" button

5. **GIVEN** I click "Flag for Review" on an article  
   **WHEN** I select a reason (Incorrect zone, Spam/irrelevant, Duplicate, Sensitive content, Other)  
   **AND** optionally add a note  
   **THEN** the article is flagged in the system  
   **AND** appears in the Flagged Articles queue for administrator review

### Performance Requirements
- Search results must return within 2 seconds for queries up to 100 characters
- Article list must support pagination (50 articles per page)
- Semantic search uses pre-computed embeddings (no real-time embedding)

### Priority: P1 (Should Have)
### Story Points: 13
### Dependencies: US-2.1

---

## US-2.3: Entity Extraction and Knowledge Graph

**As the** system  
**I want to** automatically extract entities from ingested articles and build a knowledge graph  
**So that** analysts can understand relationships between actors, organizations, and events

### Acceptance Criteria

1. **GIVEN** a new article is ingested  
   **WHEN** the entity extraction pipeline runs  
   **THEN** the system extracts:
   - People (name, title/role if mentioned, nationality if mentioned)
   - Organizations (name, type: government/company/NGO/military/other)
   - Locations (name, type: country/city/region, coordinates if resolvable)
   - Events (type, date if mentioned, participants)
   **AND** each entity has a confidence score (0.0-1.0)

2. **GIVEN** an extracted entity  
   **WHEN** the entity matches an existing entity in the knowledge graph (fuzzy matching)  
   **THEN** the system links the mention to the existing entity  
   **AND** updates the entity's mention count and last seen date  
   **WHEN** the entity does not match any existing entity  
   **THEN** the system creates a new entity record  
   **AND** queues it for potential human verification if confidence < 0.8

3. **GIVEN** I am on the Knowledge Graph page  
   **WHEN** I search for entity "Mohammed bin Salman"  
   **THEN** I see the entity profile with:
   - Canonical name and aliases
   - Entity type and role
   - Mention count (total, last 7 days, last 30 days)
   - Related entities (co-mentioned frequently)
   - Recent articles mentioning this entity
   - Zones where entity is most mentioned

4. **GIVEN** I am viewing an entity profile  
   **WHEN** I click "View Relationships"  
   **THEN** I see a network visualization showing:
   - Direct relationships to other entities
   - Relationship type (e.g., "leader of", "met with", "criticized")
   - Relationship strength (based on co-mention frequency)
   - Filter by relationship type, time period

5. **GIVEN** the entity extraction identifies "MBS" and "Mohammed bin Salman"  
   **WHEN** the deduplication process runs  
   **THEN** the system recognizes these as the same entity  
   **AND** merges them under a canonical name  
   **AND** preserves all aliases for future matching

### Entity Resolution Rules
- Case-insensitive matching
- Alias resolution using predefined alias database
- Fuzzy matching threshold: 0.85 similarity
- Manual override capability for incorrect merges

### Priority: P2 (Nice to Have)
### Story Points: 21
### Dependencies: US-2.1, US-2.2

---

# EPIC 3: STORY SELECTION

## US-3.1: Automatic Story Candidate Generation

**As the** system  
**I want to** automatically identify candidate stories from ingested articles  
**So that** the most significant geopolitical developments are surfaced for analysis

### Acceptance Criteria

1. **GIVEN** the collection pipeline runs (every 4 hours by default)  
   **WHEN** new articles have been ingested since last run  
   **THEN** the system generates story candidates by:
   - Clustering related articles (same event covered by multiple sources)
   - Identifying significant events based on signal detection rules
   - Filtering out routine/non-news content

2. **GIVEN** a cluster of articles about the same event  
   **WHEN** the story candidate is created  
   **THEN** the candidate record includes:
   - Auto-generated headline (synthesized from article titles)
   - Summary (extracted key points from articles)
   - Source articles (linked, with source tiers noted)
   - Primary zone (detected from content)
   - Secondary zones (if cross-regional story)
   - Signal type (Breaking Event, Slow Burn, Weak Signal, Counter-Consensus, Structural Shift)

3. **GIVEN** a story was covered in a previous newsletter  
   **WHEN** new articles about the same story are detected  
   **THEN** the system checks for "material development":
   - New significant facts
   - Major escalation/de-escalation
   - New actors involved
   - Resolution of previously open questions
   **IF** material development detected:
   **THEN** create new candidate with "FOLLOW-UP" tag and link to previous coverage  
   **ELSE** do not create duplicate candidate

4. **GIVEN** the story candidate generation completes  
   **WHEN** I view the Candidate Queue  
   **THEN** I see all candidates from the last collection run  
   **AND** candidates are grouped by zone  
   **AND** I can see: headline, source count, signal type, auto-score (preliminary)

5. **GIVEN** fewer than 20 candidates are generated in a collection cycle  
   **WHEN** the cycle completes  
   **THEN** the system logs a warning "Low candidate volume"  
   **AND** alerts administrators if this persists for 2+ cycles

### Story Clustering Algorithm
- Embedding-based similarity clustering
- Minimum 2 sources required to form a cluster
- Time window: 48 hours for clustering
- Entity overlap threshold: 0.6

### Priority: P0 (Must Have)
### Story Points: 21
### Dependencies: US-2.1, US-2.3

---

## US-3.2: Score Story Candidates

**As the** system  
**I want to** score story candidates across 8 dimensions  
**So that** the most important and analytically rich stories are selected for deep analysis

### Acceptance Criteria

1. **GIVEN** a story candidate is created  
   **WHEN** the scoring pipeline runs  
   **THEN** the system assigns scores (1-10) for each dimension:
   
   | Dimension | Scoring Criteria |
   |-----------|------------------|
   | Regional Impact | How significantly does this affect the primary zone? (population affected, policy implications, conflict potential) |
   | Global Systemic Impact | Does this affect international order, great power relations, global norms? |
   | Novelty | Is this genuinely new? Penalize if similar story in last 7 days. Bonus for "first" events. |
   | Analytical Richness | How much is there to unpack? (multiple actors, hidden motivations, complex causation) |
   | Interconnection Potential | Does this connect to other ongoing stories or zones? |
   | Source Quality | What tier are the sources? Agreement across sources? |
   | Underreporting | Is this under-covered relative to importance? (inverse of media attention) |
   | Audience Relevance | Does this matter for understanding how power works? |

2. **GIVEN** dimension scores are assigned  
   **WHEN** the total score is calculated  
   **THEN** the system applies weighted formula:
   ```
   total = (regional × 1.0) + (global × 1.2) + (novelty × 1.5) + 
           (richness × 1.3) + (interconnection × 1.0) + 
           (source_quality × 1.0) + (underreporting × 1.2) + 
           (audience × 1.0)
   total_normalized = total / 9.2  # Sum of weights
   ```
   **AND** the total score is stored with the candidate

3. **GIVEN** I am viewing a candidate's score details  
   **WHEN** I click "View Scoring Breakdown"  
   **THEN** I see each dimension score with:
   - The numeric score (1-10)
   - Brief explanation of why this score was assigned
   - Evidence cited (article excerpts, source references)

4. **GIVEN** I disagree with an auto-assigned score  
   **WHEN** I click "Override Score" for a dimension  
   **AND** I enter a new score and justification  
   **THEN** the system updates the score and recalculates the total  
   **AND** marks the candidate as "Manually Adjusted"  
   **AND** logs the override with user identity, original score, new score, justification

5. **GIVEN** scoring is complete for all candidates  
   **WHEN** I view the Candidate Queue sorted by score  
   **THEN** the highest-scoring candidates appear first  
   **AND** I can filter by: minimum score, zone, signal type, manual adjustment status

### Scoring Model
- Uses HIGH tier model for scoring (cost-effective, sufficiently accurate)
- Scoring prompt includes few-shot examples of well-scored candidates
- Novelty scoring requires access to last 7 days of published stories

### Priority: P0 (Must Have)
### Story Points: 13
### Dependencies: US-3.1

---

## US-3.3: Select Stories for Daily Edition

**As an** editor  
**I want to** select which stories will be featured in the daily newsletter  
**So that** I can ensure quality, diversity, and editorial judgment in the final product

### Acceptance Criteria

1. **GIVEN** I am on the Story Selection page for today's edition  
   **WHEN** I view the default state  
   **THEN** I see:
   - Left panel: All scored candidates (sorted by score, grouped by zone)
   - Right panel: Selected stories (empty initially, target: 5)
   - Top bar: Selection rules and warnings

2. **GIVEN** the system has scored candidates  
   **WHEN** I click "Auto-Select Top 5"  
   **THEN** the system selects 5 stories optimizing for:
   - Highest total scores
   - At least 3 different regions represented
   - At least 1 "slow burn" or structural story
   - At least 1 under-reported story (underreporting score ≥ 7)
   - No more than 2 stories from the same region
   - No more than 1 US-focused story (unless scores exceptionally high)
   **AND** displays the selected stories in the right panel  
   **AND** shows which rules influenced selection

3. **GIVEN** auto-selection violates a rule  
   **WHEN** the selection is displayed  
   **THEN** the system shows a warning (e.g., "Only 2 regions represented - consider diversifying")  
   **AND** suggests alternative candidates that would satisfy the rule

4. **GIVEN** I want to manually adjust the selection  
   **WHEN** I drag a candidate from left panel to right panel  
   **THEN** the story is added to the selection  
   **AND** if selection now has > 5 stories, the system prompts me to remove one  
   **WHEN** I drag a story from right panel back to left panel  
   **THEN** the story is removed from the selection

5. **GIVEN** I have finalized my selection  
   **WHEN** I click "Confirm Selection"  
   **THEN** the system validates:
   - Exactly 5 stories selected
   - All selection rules satisfied (or warnings acknowledged)
   - No duplicate stories from previous 7 days (unless marked as follow-up)
   **IF** validation passes:
   **THEN** the selection is locked  
   **AND** the analysis pipeline is triggered for selected stories  
   **IF** validation fails:
   **THEN** display specific errors and prevent confirmation

6. **GIVEN** the selection is confirmed  
   **WHEN** the analysis pipeline starts  
   **THEN** the Selection page shows status: "Analysis in progress"  
   **AND** I cannot modify the selection without administrator override

### Priority: P0 (Must Have)
### Story Points: 13
### Dependencies: US-3.2

---

# EPIC 4: ANALYSIS PIPELINE

## US-4.1: Execute Foundation Analysis (Pass 1)

**As the** system  
**I want to** perform foundation analysis on selected stories  
**So that** the factual basis, context, and actor landscape is established before deep analysis

### Acceptance Criteria

1. **GIVEN** stories are confirmed for today's edition  
   **WHEN** the analysis pipeline starts  
   **THEN** Pass 1 executes in parallel for all 5 stories  
   **AND** within Pass 1, the following agents run in parallel:
   - Factual Reconstruction Agent
   - Context Builder Agent
   - Actor Profiler Agent
   - Source Retrieval Agent

2. **GIVEN** the Factual Reconstruction Agent runs  
   **WHEN** it completes  
   **THEN** the output includes:
   - Timeline of events (chronological, with timestamps and sources)
   - Key facts (each fact with: statement, source(s), confidence level)
   - Actors involved (names, roles in this event)
   - Information gaps (what we don't know)
   **AND** each fact is linked to at least 1 source  
   **AND** confidence levels are: HIGH (2+ independent sources), MEDIUM (1 quality source), LOW (single non-tier-1 source)

3. **GIVEN** a foundation agent completes its initial output  
   **WHEN** the self-critique phase runs  
   **THEN** the system uses the same model tier to critique the output  
   **AND** identifies issues (if any) with severity scores  
   **IF** any issue has severity > 0.3:
   **THEN** the system triggers a revision pass  
   **AND** incorporates critique feedback into revised output  
   **ELSE** the output is accepted as-is

4. **GIVEN** all Pass 1 agents complete (including any revisions)  
   **WHEN** Quality Gate 1 evaluates the outputs  
   **THEN** the gate checks:
   - Source count ≥ 5 per story
   - Source diversity ≥ 3 independent outlets
   - Timeline has no contradictions
   - All key actors identified
   **IF** score ≥ 0.80:
   **THEN** Pass 1 is complete, proceed to Pass 2  
   **ELSE** trigger targeted re-retrieval and re-analysis (max 2 retries)

5. **GIVEN** Pass 1 fails Quality Gate 1 after 2 retries  
   **WHEN** the final retry fails  
   **THEN** the story is flagged for human review  
   **AND** the pipeline continues with other stories  
   **AND** administrator is alerted with specific failure reasons

### Performance Requirements
- Pass 1 should complete within 30 minutes for all 5 stories
- Each agent should complete within 5 minutes (excluding retries)
- Parallel execution must not exceed rate limits

### Priority: P0 (Must Have)
### Story Points: 21
### Dependencies: US-3.3

---

## US-4.2: Execute Deep Analysis (Pass 2)

**As the** system  
**I want to** perform deep motivation and causal chain analysis  
**So that** the "why" and "so what" of each story is thoroughly examined

### Acceptance Criteria

1. **GIVEN** Pass 1 is complete for a story  
   **WHEN** Pass 2 begins  
   **THEN** the following agents execute using FRONTIER tier models:
   - Motivation Analyst (requires Pass 1 outputs)
   - Chain Mapper (requires Pass 1 outputs)
   - Subtlety Analyst (requires Pass 1 outputs)

2. **GIVEN** the Motivation Analyst runs  
   **WHEN** it completes  
   **THEN** the output includes:

   **Layer 1 - Individual Decision-Maker:**
   - Name and role of key decision-maker(s)
   - Political position analysis
   - Domestic political needs
   - Psychology/worldview assessment
   - Personal relationships relevant to decision
   - Legacy considerations
   - Confidence level and evidence cited

   **Layer 2 - Institutional Interests:**
   - Foreign ministry interests
   - Military/intelligence interests
   - Economic actors who benefit
   - Institutional momentum assessment
   - Confidence level and evidence cited

   **Layer 3 - Structural Pressures:**
   - Systemic position pressures
   - Threat environment
   - Economic structure constraints
   - Geographic imperatives
   - Confidence level and evidence cited

   **Layer 4 - Opportunistic Window:**
   - What changed to create opening
   - Whose position shifted
   - What constraint relaxed
   - What's coming that creates urgency
   - Confidence level and evidence cited

   **Synthesis:**
   - Primary driver (which layer does most work)
   - Enabling conditions
   - Alternative hypotheses (minimum 2)
   - What evidence would change assessment

3. **GIVEN** the Chain Mapper runs  
   **WHEN** it completes  
   **THEN** the output includes:

   **Forward Chains (minimum 4th order):**
   - 1st order effects (direct consequences)
   - 2nd order effects (responses to 1st order)
   - 3rd order effects (systemic adaptations)
   - 4th order effects (equilibrium shifts)
   - 5th order effects (chain interactions, if applicable)
   - Confidence decay noted at each level

   **Backward Chains (Cui Bono):**
   - Who benefits at each order
   - Hidden beneficiaries analysis
   - Means/motive/opportunity for each

   **Chain Intersections:**
   - How this chain interacts with other ongoing chains
   - Emergent dynamics

4. **GIVEN** a Pass 2 agent produces output  
   **WHEN** self-critique runs  
   **AND** issues with severity > 0.3 are identified  
   **THEN** the system triggers revision  
   **AND** re-critiques the revision  
   **AND** continues revision loop until severity < 0.3 or max revisions (2) reached

5. **GIVEN** all Pass 2 agents complete  
   **WHEN** Quality Gate 2 evaluates  
   **THEN** the gate checks:
   - All 4 motivation layers present and substantive
   - Chain depth ≥ 4 orders
   - Backward tracing completed
   - Alternative hypotheses ≥ 2
   - Self-critique issues resolved
   **IF** score ≥ 0.85:
   **THEN** Pass 2 complete, proceed to Pass 3  
   **ELSE** trigger targeted re-analysis (max 2 retries)

### Priority: P0 (Must Have)
### Story Points: 34
### Dependencies: US-4.1

---

## US-4.3: Execute Adversarial Review (Pass 3)

**As the** system  
**I want to** challenge the analysis through adversarial debate  
**So that** weak arguments, hidden assumptions, and overconfident claims are identified and addressed

### Acceptance Criteria

1. **GIVEN** Pass 2 is complete for a story  
   **WHEN** Pass 3 begins  
   **THEN** the Debate Protocol initiates with:
   - Advocate Agent (defends the analysis)
   - Challenger Agent (attacks the analysis)
   - Judge Agent (adjudicates)

2. **GIVEN** the Debate Protocol runs  
   **WHEN** Round 1 begins  
   **THEN** the Advocate presents the analysis with supporting evidence  
   **THEN** the Challenger attacks using strategies:
   - Logical fallacy detection
   - Alternative explanation generation
   - Hidden assumption surfacing
   - Missing evidence identification
   - Overconfidence flagging
   - Selection bias challenges
   **AND** each challenge includes: specific passage cited, issue type, severity (Critical/Major/Minor), suggested fix

3. **GIVEN** the Challenger produces challenges  
   **WHEN** Round 2 begins  
   **THEN** the Advocate responds to each challenge:
   - Concede (accept the critique, modify analysis)
   - Rebut (defend with additional evidence)
   - Clarify (address misunderstanding)
   **THEN** the Challenger responds to rebuttals  
   **AND** Round 3 follows same pattern

4. **GIVEN** 3 debate rounds complete  
   **WHEN** the Judge Agent evaluates  
   **THEN** the Judge produces:
   - Issues resolved (with resolution method)
   - Issues unresolved (with severity)
   - Modifications to original analysis (if any)
   - Final confidence adjustment (increase/decrease from original)
   - Recommendation: Accept / Accept with modifications / Reject for human review

5. **GIVEN** the Debate Protocol completes  
   **WHEN** parallel verification agents run  
   **THEN** the following execute concurrently:
   - Fact-Checker: Verifies all factual claims against sources
   - Source-Verifier: Checks source quality and independence
   - Logic-Auditor: Validates causal reasoning
   - Bias-Detector: Identifies geographic, ideological, or analytical biases

6. **GIVEN** all Pass 3 components complete  
   **WHEN** Quality Gate 3 evaluates  
   **THEN** the gate checks:
   - Debate unresolved issues ≤ 2 Major (0 Critical)
   - Fact-check pass rate ≥ 95%
   - No critical logic flaws
   - Bias assessment acceptable
   **IF** score ≥ 0.90:
   **THEN** Pass 3 complete, proceed to Pass 4  
   **ELSE IF** score ≥ 0.80:
   **THEN** flag for human review, continue to Pass 4  
   **ELSE** reject story, alert administrator

### Debate Configuration
- Maximum rounds: 3 (configurable)
- Early termination: If Challenger concedes all major points
- Model tier: FRONTIER for all debate agents
- Debate transcript saved for audit

### Priority: P0 (Must Have)
### Story Points: 34
### Dependencies: US-4.2

---

## US-4.4: Execute Supplementary Analysis (Pass 3b)

**As the** system  
**I want to** enrich the analysis with theory, history, geography, and shockwave analysis  
**So that** the article has intellectual depth and practical implications

### Acceptance Criteria

1. **GIVEN** Pass 2 is complete (runs in parallel with Pass 3 debate)  
   **WHEN** supplementary analysis begins  
   **THEN** the following agents run in parallel (HIGH tier):
   - Theory Application Agent
   - Historical Parallel Agent
   - Geometry Analysis Agent
   - Shockwave Analysis Agent
   - Uncertainty Calibration Agent

2. **GIVEN** the Theory Application Agent runs  
   **WHEN** it completes  
   **THEN** the output includes:
   - Relevant IR theory frameworks (realism, liberalism, constructivism concepts)
   - Relevant strategic frameworks (deterrence, coercion, alliance theory)
   - For each framework: concept name, plain-English explanation, how it applies to this case
   - Theoretical predictions and their confidence levels
   **AND** concepts are explained as if reader is intelligent but not a specialist

3. **GIVEN** the Historical Parallel Agent runs  
   **WHEN** it completes  
   **THEN** the output includes:
   - 2-3 most relevant historical parallels
   - For each parallel:
     - What happened (brief summary)
     - Similarities to current case (specific)
     - Differences from current case (disanalogies)
     - Lessons that may apply
     - Lessons that may NOT apply
   - Why other obvious parallels were not chosen

4. **GIVEN** the Geometry Analysis Agent runs  
   **WHEN** it completes  
   **THEN** the output includes:
   - Map-based insights (what geography reveals)
   - Chokepoints affected
   - Access/denial implications
   - Network position changes
   - Distance/logistics considerations

5. **GIVEN** the Shockwave Analysis Agent runs  
   **WHEN** it completes  
   **THEN** the output includes:
   - Geographic ripples (which neighboring states affected, how)
   - Economic transmission (trade, commodities, supply chains, markets)
   - Institutional effects (international orgs, alliances, norms)
   - Humanitarian dimensions (populations affected, displacement)
   - Precedent effects (what's now considered possible/acceptable)

6. **GIVEN** the Uncertainty Calibration Agent runs  
   **WHEN** it completes  
   **THEN** it reviews ALL analysis outputs and produces:
   - Confidence levels for each major claim (calibrated)
   - Information gaps (what we don't know)
   - Expert disagreements (where credible analysts differ)
   - Falsification criteria (what would prove us wrong)
   - What to watch (events that would confirm/disconfirm)

### Priority: P0 (Must Have)
### Story Points: 21
### Dependencies: US-4.2

---

## US-4.5: Execute Production (Pass 4)

**As the** system  
**I want to** synthesize all analysis into a polished article  
**So that** the final output meets Undertow voice and quality standards

### Acceptance Criteria

1. **GIVEN** Pass 3 (adversarial + supplementary) is complete  
   **WHEN** Pass 4 begins  
   **THEN** the Outline Generator creates article structure:
   1. THE HOOK (300-500 words)
   2. WHAT HAPPENED (600-1,000 words)
   3. THE ACTORS (500-800 words)
   4. THE BACKSTORY (600-900 words)
   5. THE MOTIVATION ANALYSIS (800-1,200 words)
   6. THE SUBTLETIES (600-900 words)
   7. THE CHAINS (1,000-1,500 words)
   8. THE GEOMETRY (400-600 words)
   9. THE THEORY & HISTORY (600-1,000 words)
   10. THE SHOCKWAVES (500-700 words)
   11. WHAT WE DON'T KNOW (300-500 words)
   12. THE TAKEAWAY (300-400 words)

2. **GIVEN** the outline is generated  
   **WHEN** Section Writers execute (parallel, FRONTIER tier)  
   **THEN** each section is written according to:
   - Word count target for that section
   - Undertow voice guidelines
   - Required content from analysis packages
   **AND** each section includes inline source citations

3. **GIVEN** all sections are written  
   **WHEN** the Integrator Agent runs  
   **THEN** it produces a unified article that:
   - Flows as coherent narrative (not checklist)
   - Has consistent voice throughout
   - Transitions smoothly between sections
   - Removes redundancy between sections
   - Maintains consistent terminology

4. **GIVEN** the integrated draft is produced  
   **WHEN** the Voice Calibration Agent runs  
   **THEN** it checks for and corrects:
   - Forbidden phrases (see list)
   - Passive voice (where agency should be clear)
   - Jargon without explanation
   - Overconfident assertions without hedging
   - Sentence variety (flags if too uniform)
   - Tone inconsistencies

5. **GIVEN** voice calibration is complete  
   **WHEN** Self-Edit Pass 1 runs (FRONTIER)  
   **THEN** the agent reviews the article as if editing someone else's work  
   **AND** makes improvements to:
   - Clarity (rewrite confusing sentences)
   - Concision (remove unnecessary words)
   - Impact (strengthen weak arguments)
   - Flow (improve transitions)

6. **GIVEN** Self-Edit Pass 1 is complete  
   **WHEN** Self-Edit Pass 2 runs (HIGH tier)  
   **THEN** the agent does a final polish focusing on:
   - Typos and grammar
   - Citation completeness
   - Fact-check any new claims introduced in editing
   - Word count compliance (5,000-8,000)

7. **GIVEN** both edit passes complete  
   **WHEN** Quality Gate 4 evaluates  
   **THEN** the gate checks:
   - Voice consistency score ≥ 0.85
   - No forbidden phrases present
   - Word count in range
   - All sections present and substantive
   - All source citations present
   - Overall quality score ≥ 0.90
   **IF** passes:
   **THEN** article is ready for newsletter assembly  
   **ELSE** trigger additional edit pass or human review

### Forbidden Phrases List
- "In today's interconnected world"
- "Time will tell"
- "Remains to be seen"
- "Violence erupted" (passive)
- "Tensions escalated" (agentless)
- "It is what it is"
- "At the end of the day"
- "Going forward"
- "On the ground"

### Priority: P0 (Must Have)
### Story Points: 34
### Dependencies: US-4.3, US-4.4

---

# EPIC 5: NEWSLETTER ASSEMBLY & PUBLICATION

## US-5.1: Generate Newsletter Preamble

**As the** system  
**I want to** generate a compelling preamble that ties the day's stories together  
**So that** readers understand the thematic connections and are drawn into the edition

### Acceptance Criteria

1. **GIVEN** all 5 articles for today are complete  
   **WHEN** preamble generation begins  
   **THEN** the system analyzes all 5 articles for:
   - Common themes across stories
   - Unexpected connections between stories
   - The "meta-narrative" of the day
   - What's notably absent from today's news

2. **GIVEN** thematic analysis is complete  
   **WHEN** the Preamble Writer generates content  
   **THEN** the preamble includes:

   **Opening Hook (200-300 words):**
   - What kind of day/week was it in world affairs?
   - The animating theme or observation
   - Should feel like editorial voice, not summary

   **Through-Line (400-500 words):**
   - Connective tissue between the 5 stories
   - Pattern(s) linking disparate events
   - Why these stories together tell us something

   **What Else Matters (300-400 words):**
   - 3-5 stories not featured but worth noting
   - Brief (2-3 sentences each) but substantive
   - With links to sources

   **The Observation (100-200 words):**
   - Meta-comment on coverage, an unexpected connection, or a provocation
   - Should be memorable/quotable
   - Should demonstrate editorial personality

3. **GIVEN** the preamble is generated  
   **WHEN** voice calibration runs  
   **THEN** it ensures:
   - First-person plural ("we") used appropriately
   - Direct address to reader where effective
   - Wit present but not forced
   - No false equivalences or both-sides-ism
   - Takes a point of view

4. **GIVEN** voice calibration is complete  
   **WHEN** the preamble is finalized  
   **THEN** word count is 1,000-1,500 words total  
   **AND** the preamble passes quality check (score ≥ 0.85)

### Priority: P0 (Must Have)
### Story Points: 13
### Dependencies: US-4.5

---

## US-5.2: Assemble Complete Newsletter

**As the** system  
**I want to** assemble all components into the final newsletter  
**So that** it's ready for publication with consistent formatting

### Acceptance Criteria

1. **GIVEN** preamble and all 5 articles are complete  
   **WHEN** assembly begins  
   **THEN** the system creates newsletter with structure:
   ```
   1. PREAMBLE (1,000-1,500 words)
   2. FEATURE 1 (5,000-8,000 words)
      - Headline + Subhead
      - Zone/Theme tags
      - Read time estimate
      - Full article
      - Source list with links
      - Related previous coverage (internal links)
   3. INTERSTITIAL ("Meanwhile..." - 200 words)
   4. FEATURE 2
   5. INTERSTITIAL
   6. FEATURE 3
   7. INTERSTITIAL
   8. FEATURE 4
   9. INTERSTITIAL
   10. FEATURE 5
   11. "WORTH YOUR TIME" section (external link recommendations)
   12. CORRECTIONS (if any from previous editions)
   13. THE CLOSE (200-300 words)
   ```

2. **GIVEN** the structure is assembled  
   **WHEN** formatting is applied  
   **THEN** the system:
   - Generates table of contents with anchor links
   - Calculates total read time
   - Applies consistent heading styles
   - Formats all citations consistently
   - Creates source bibliography at end of each article

3. **GIVEN** formatting is complete  
   **WHEN** final validation runs  
   **THEN** the system checks:
   - All internal links work
   - All external links are valid (HTTP 200)
   - No broken images or embeds
   - Total word count displayed
   - All articles have complete metadata
   - Regional diversity rules met

4. **GIVEN** validation passes  
   **WHEN** the editor reviews the assembled newsletter  
   **THEN** they see a preview that matches final output format  
   **AND** can make minor text edits without re-running pipeline  
   **AND** can approve for publication or request revisions

### Priority: P0 (Must Have)
### Story Points: 13
### Dependencies: US-5.1

---

## US-5.3: Publish Newsletter

**As an** editor  
**I want to** publish the completed newsletter to subscribers  
**So that** readers receive the daily intelligence briefing

### Acceptance Criteria

1. **GIVEN** the newsletter is assembled and approved  
   **WHEN** I click "Publish"  
   **THEN** I see a confirmation dialog with:
   - Total word count
   - Estimated read time
   - Subscriber count
   - Scheduled send time (or "Immediately")
   - Preview of email subject line

2. **GIVEN** I confirm publication  
   **WHEN** the system processes the request  
   **THEN** the newsletter is:
   - Saved to the archive with permanent URL
   - Queued for email delivery to all active subscribers
   - Published to the web (if web publication enabled)
   - RSS feed updated

3. **GIVEN** email delivery begins  
   **WHEN** emails are sent  
   **THEN** the system:
   - Sends in batches to avoid spam filters
   - Tracks delivery status (sent, delivered, bounced, opened)
   - Reports delivery metrics on dashboard

4. **GIVEN** publication is complete  
   **WHEN** I view the Publication Log  
   **THEN** I see:
   - Publication timestamp
   - Archive URL
   - Email delivery stats (updated in real-time)
   - Any delivery errors

5. **GIVEN** a critical error is discovered post-publication  
   **WHEN** I click "Issue Correction"  
   **THEN** I can:
   - Edit the archived version
   - Add correction notice (displayed prominently)
   - Optionally send correction email to subscribers
   - Log the correction with reason

### Priority: P0 (Must Have)
### Story Points: 8
### Dependencies: US-5.2

---

# EPIC 6: HUMAN REVIEW & ESCALATION

## US-6.1: View Human Review Queue

**As an** editor/analyst  
**I want to** see all items requiring human review  
**So that** I can address issues that the automated system couldn't resolve

### Acceptance Criteria

1. **GIVEN** I am on the Human Review page  
   **WHEN** I view the queue  
   **THEN** I see items sorted by priority (Critical → High → Medium → Low)  
   **AND** each item shows:
   - Story headline
   - Escalation reason
   - Severity level
   - Time in queue
   - Assigned reviewer (if any)

2. **GIVEN** I click on a review item  
   **WHEN** the detail view opens  
   **THEN** I see the Escalation Package containing:
   - Draft article content
   - Specific issues flagged (with locations highlighted)
   - Analysis chain (outputs from each pass)
   - Debate transcript (if debate triggered escalation)
   - Source documents (relevant retrieved sources)
   - Suggested actions

3. **GIVEN** I am viewing an escalation item  
   **WHEN** I click "Claim for Review"  
   **THEN** the item is assigned to me  
   **AND** other reviewers see it as "In Review by [my name]"  
   **AND** a 2-hour timer starts (configurable)

4. **GIVEN** I have claimed an item  
   **WHEN** I complete my review  
   **THEN** I can:
   - Approve: Analysis is acceptable, continue pipeline
   - Approve with Edits: Make changes, then continue
   - Request Re-analysis: Send back to specific pipeline stage with notes
   - Reject: Kill the story, provide reason

5. **GIVEN** I take action on a review item  
   **WHEN** I click Submit  
   **THEN** the system:
   - Logs my action with timestamp and any notes
   - Routes the story appropriately
   - Removes item from queue
   - Updates metrics (time in review, outcome)

### Escalation Triggers (Reference)
- Factual contradiction detected
- Low confidence (< 0.5) on key claim
- Debate produced unresolved critical issues
- Quality gate failed after max retries
- High-stakes actors/events involved
- System explicitly flagged for human judgment

### Priority: P0 (Must Have)
### Story Points: 13
### Dependencies: US-4.3

---

## US-6.2: Edit Article in Review

**As an** editor  
**I want to** make edits to an article during human review  
**So that** I can fix issues without re-running the entire pipeline

### Acceptance Criteria

1. **GIVEN** I am reviewing an article  
   **WHEN** I click "Edit Article"  
   **THEN** I enter an editing interface with:
   - Full article text (rich text editor)
   - Tracked changes mode (shows my edits)
   - Side panel with original analysis outputs
   - Source quick-reference

2. **GIVEN** I am editing  
   **WHEN** I make changes to text  
   **THEN** changes are tracked and highlighted  
   **AND** I can add editorial notes to explain changes  
   **AND** word count updates in real-time

3. **GIVEN** I want to change a factual claim  
   **WHEN** I select the claim text  
   **THEN** I can:
   - Edit the claim text
   - Update/add source citation
   - Adjust confidence level
   - Add editorial note explaining the change

4. **GIVEN** I have made edits  
   **WHEN** I click "Save Edits"  
   **THEN** the system:
   - Saves edited version (preserving original)
   - Runs quick validation (format, word count, forbidden phrases)
   - Shows diff between original and edited versions

5. **GIVEN** I have saved edits  
   **WHEN** I click "Approve with Edits"  
   **THEN** the edited version proceeds in the pipeline  
   **AND** the audit log shows original, edited, and my identity  
   **AND** the article is flagged as "Manually Edited"

### Priority: P1 (Should Have)
### Story Points: 13
### Dependencies: US-6.1

---

# EPIC 7: MONITORING & ANALYTICS

## US-7.1: View Pipeline Dashboard

**As an** operator  
**I want to** see real-time status of the daily pipeline  
**So that** I can monitor progress and identify issues quickly

### Acceptance Criteria

1. **GIVEN** I am on the Dashboard  
   **WHEN** I view the Pipeline Status section  
   **THEN** I see:
   ```
   Collection   [████████████████████] 100% ✓ Complete
   Analysis     [████████████░░░░░░░░]  62% ⏳ In Progress
   Red Team     [░░░░░░░░░░░░░░░░░░░░]   0% ⏸ Waiting
   Production   [░░░░░░░░░░░░░░░░░░░░]   0% ⏸ Waiting
   Assembly     [░░░░░░░░░░░░░░░░░░░░]   0% ⏸ Waiting
   
   ETA to Publication: 8h 23m
   ```

2. **GIVEN** I click on "Analysis" stage  
   **WHEN** the detail panel opens  
   **THEN** I see per-story status:
   - Story 1: Pass 2 - Motivation Analysis ⏳
   - Story 2: Pass 2 - Chain Mapping ⏳
   - Story 3: Pass 1 - Quality Gate ✓
   - Story 4: Pass 2 - Subtlety Analysis ⏳
   - Story 5: Pass 1 - Context Building ⏳

3. **GIVEN** I view the Cost Tracking section  
   **WHEN** costs are accumulating  
   **THEN** I see:
   - Today's spend: $XX.XX / $100 budget
   - Visual progress bar
   - Breakdown by phase
   - Breakdown by model tier
   - 7-day trend chart

4. **GIVEN** I view the Quality Metrics section  
   **WHEN** metrics are displayed  
   **THEN** I see:
   - Average confidence score (today)
   - Red team pass rate
   - Source diversity average
   - Human review rate
   - Quality gate retry rate

5. **GIVEN** an alert condition occurs  
   **WHEN** the alert fires  
   **THEN** the Dashboard shows:
   - Alert banner at top
   - Alert in sidebar feed with timestamp
   - Visual indicator on affected component

### Priority: P0 (Must Have)
### Story Points: 21
### Dependencies: US-4.5

---

## US-7.2: View Cost Analytics

**As a** system administrator  
**I want to** see detailed cost analytics  
**So that** I can optimize spending and forecast budgets

### Acceptance Criteria

1. **GIVEN** I am on the Cost Analytics page  
   **WHEN** I select a date range  
   **THEN** I see:
   - Total spend for period
   - Daily breakdown chart
   - Average cost per article
   - Cost trend (increasing/decreasing)

2. **GIVEN** I view cost breakdown  
   **WHEN** I select "By Model"  
   **THEN** I see:
   | Model | Requests | Tokens (In) | Tokens (Out) | Cost | % of Total |
   |-------|----------|-------------|--------------|------|------------|
   | claude-sonnet-4 | 1,234 | 5.2M | 890K | $45.23 | 45% |
   | gpt-4o | 567 | 2.1M | 340K | $12.34 | 12% |
   | ... | ... | ... | ... | ... | ... |

3. **GIVEN** I view cost breakdown  
   **WHEN** I select "By Task Type"  
   **THEN** I see:
   | Task Type | Executions | Avg Tokens | Avg Cost | Total Cost |
   |-----------|------------|------------|----------|------------|
   | motivation_analysis | 150 | 18,234 | $1.12 | $168.00 |
   | chain_mapping | 150 | 22,456 | $1.38 | $207.00 |
   | ... | ... | ... | ... | ... |

4. **GIVEN** I view cost breakdown  
   **WHEN** I select "By Article"  
   **THEN** I see cost for each published article with breakdown by pass

5. **GIVEN** I want to export data  
   **WHEN** I click "Export CSV"  
   **THEN** I receive a detailed CSV with all cost records for the period

### Priority: P1 (Should Have)
### Story Points: 13
### Dependencies: US-7.1

---

## US-7.3: Track Prediction Accuracy

**As an** analyst  
**I want to** track how accurate our predictions have been  
**So that** we can calibrate confidence and improve our methodology

### Acceptance Criteria

1. **GIVEN** an article makes a prediction  
   **WHEN** the article is published  
   **THEN** the system extracts and logs:
   - Prediction text
   - Confidence level stated
   - Timeframe (if specified)
   - Conditions for resolution
   - Article ID and publication date

2. **GIVEN** I am on the Prediction Tracker page  
   **WHEN** I view open predictions  
   **THEN** I see predictions awaiting resolution:
   - Prediction summary
   - Confidence stated
   - Days since prediction
   - Expected resolution date (if timeframe given)
   - "Resolve" button

3. **GIVEN** I click "Resolve" on a prediction  
   **WHEN** I select outcome  
   **THEN** I can choose:
   - Correct: Prediction was accurate
   - Incorrect: Prediction was wrong
   - Partially Correct: Some elements correct
   - Indeterminate: Cannot be resolved
   **AND** I add notes explaining the resolution  
   **AND** I link to evidence (article/source)

4. **GIVEN** predictions have been resolved  
   **WHEN** I view accuracy statistics  
   **THEN** I see:
   - Overall accuracy rate
   - Accuracy by confidence level (calibration check)
   - Accuracy by zone/topic
   - Accuracy over time (trend)

5. **GIVEN** I view calibration analysis  
   **WHEN** data is sufficient (50+ resolved predictions)  
   **THEN** the system shows:
   - Expected vs. actual accuracy by confidence bucket
   - Calibration curve
   - Recommendations (e.g., "High confidence predictions are overconfident")

### Priority: P2 (Nice to Have)
### Story Points: 13
### Dependencies: US-5.3

---

# EPIC 8: ARCHIVE & SEARCH

## US-8.1: Search Published Articles

**As a** reader  
**I want to** search the archive of published articles  
**So that** I can find past coverage on topics of interest

### Acceptance Criteria

1. **GIVEN** I am on the Archive page  
   **WHEN** I enter a search query  
   **THEN** the system searches across:
   - Article headlines
   - Article content
   - Tags (zone, theme, actors)
   **AND** returns ranked results

2. **GIVEN** I apply filters  
   **WHEN** I select:
   - Zone(s)
   - Date range
   - Theme(s)
   - Actor(s)
   **THEN** results are filtered accordingly  
   **AND** filter state is reflected in URL

3. **GIVEN** I view search results  
   **WHEN** results are displayed  
   **THEN** each result shows:
   - Headline
   - Publication date
   - Zone and theme tags
   - Excerpt with query terms highlighted
   - Read time

4. **GIVEN** I click on a result  
   **WHEN** the article loads  
   **THEN** I see the full article with:
   - All sections
   - Complete source list
   - Related articles sidebar
   - "Follow this story" button (if ongoing story)

### Priority: P1 (Should Have)
### Story Points: 13
### Dependencies: US-5.3

---

## US-8.2: Browse by Zone

**As a** reader  
**I want to** browse articles by geographic zone  
**So that** I can follow coverage of regions I care about

### Acceptance Criteria

1. **GIVEN** I am on the Zone Browser  
   **WHEN** I select a zone (e.g., "Horn of Africa")  
   **THEN** I see:
   - Zone description and key dynamics
   - Recent articles (last 30 days)
   - Top actors in this zone
   - Related zones
   - Subscribe to zone (email alerts)

2. **GIVEN** I view a zone page  
   **WHEN** I click "Coverage Map"  
   **THEN** I see visual timeline of coverage with article volume over time

3. **GIVEN** I click "Subscribe to Zone"  
   **WHEN** I enter my email  
   **THEN** I receive email alerts when articles about this zone are published

### Priority: P2 (Nice to Have)
### Story Points: 8
### Dependencies: US-8.1

---

# EPIC 9: USER MANAGEMENT

## US-9.1: Manage User Accounts

**As an** administrator  
**I want to** create and manage user accounts with roles  
**So that** appropriate people have appropriate access

### Acceptance Criteria

1. **GIVEN** I am on the User Management page  
   **WHEN** I click "Add User"  
   **THEN** I enter:
   - Email (required, valid format)
   - Name (required)
   - Role (dropdown: Admin, Editor, Analyst, Viewer)

2. **GIVEN** I create a user  
   **WHEN** the user is saved  
   **THEN** the system:
   - Sends invitation email with secure link
   - User can set password on first login
   - Account is created but inactive until password set

3. **GIVEN** I view the user list  
   **WHEN** users are displayed  
   **THEN** I see:
   - Name, email, role
   - Status (active, invited, suspended)
   - Last login
   - Actions (edit, suspend, delete)

4. **GIVEN** I click "Edit" on a user  
   **WHEN** I modify their role  
   **THEN** changes take effect immediately  
   **AND** user is logged out if their permissions decreased

### Role Permissions
| Permission | Admin | Editor | Analyst | Viewer |
|------------|-------|--------|---------|--------|
| Configure system | ✓ | | | |
| Manage users | ✓ | | | |
| Override budgets | ✓ | | | |
| Publish newsletter | ✓ | ✓ | | |
| Edit articles | ✓ | ✓ | | |
| Human review | ✓ | ✓ | ✓ | |
| Select stories | ✓ | ✓ | ✓ | |
| View dashboard | ✓ | ✓ | ✓ | ✓ |
| View analytics | ✓ | ✓ | ✓ | ✓ |
| Read articles | ✓ | ✓ | ✓ | ✓ |

### Priority: P0 (Must Have)
### Story Points: 13
### Dependencies: None

---

# ACCEPTANCE CRITERIA GLOSSARY

| Term | Definition |
|------|------------|
| **GIVEN** | The precondition or context for the scenario |
| **WHEN** | The action or trigger being tested |
| **THEN** | The expected outcome or result |
| **AND** | Additional conditions for the same outcome |
| **IF/ELSE** | Conditional branching based on state |

# PRIORITY DEFINITIONS

| Priority | Definition | Target Release |
|----------|------------|----------------|
| **P0 - Must Have** | Core functionality required for MVP | v1.0 |
| **P1 - Should Have** | Important but not blocking launch | v1.1 |
| **P2 - Nice to Have** | Enhances UX but can wait | v1.2+ |

# STORY POINT REFERENCE

| Points | Complexity | Typical Duration |
|--------|------------|------------------|
| 1-2 | Trivial | < 1 day |
| 3-5 | Simple | 1-2 days |
| 8 | Medium | 3-5 days |
| 13 | Complex | 1-2 weeks |
| 21 | Very Complex | 2-3 weeks |
| 34 | Epic-level | 3-4 weeks |

---

# APPENDIX A: COMPLETE EPIC LIST

| Epic | Stories | Total Points |
|------|---------|--------------|
| 1: System Configuration | US-1.1 to US-1.4 | 26 |
| 2: Source Ingestion | US-2.1 to US-2.3 | 47 |
| 3: Story Selection | US-3.1 to US-3.3 | 47 |
| 4: Analysis Pipeline | US-4.1 to US-4.5 | 131 |
| 5: Newsletter Assembly | US-5.1 to US-5.3 | 34 |
| 6: Human Review | US-6.1 to US-6.2 | 26 |
| 7: Monitoring | US-7.1 to US-7.3 | 47 |
| 8: Archive & Search | US-8.1 to US-8.2 | 21 |
| 9: User Management | US-9.1 | 13 |
| **TOTAL** | **26 Stories** | **392 Points** |

---

*This document represents the complete user story set for The Undertow v1.0. Stories should be refined during sprint planning with the development team.*

