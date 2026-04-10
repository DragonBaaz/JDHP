# JDHP — Expanded Implementation Plan
# For coding models: read this file completely before writing any code.
# Every section contains exact contracts, method signatures, and decision rules.

---

## CODING MODEL INSTRUCTIONS
- Language: Python 3.11+
- All agents live in `agents/` directory, one file per agent
- All agents inherit from `agents/base.py::BaseAgent`
- Orchestrator lives in `orchestrator/runner.py`
- Job state lives in `db/models.py` (SQLite via peewee)
- Config lives in `config.py` (loaded from `.env` via `python-dotenv`)
- Never hardcode API keys — always read from environment
- Every agent `run()` method must be idempotent (safe to retry)
- Log every agent action to `logs/` using Python `logging` (not print)
- All external API calls must have a retry wrapper with exponential backoff (max 3 retries)
- Type-hint everything. Use `TypedDict` for input/output contracts.

---

## REPOSITORY STRUCTURE
```
JDHP/
├── ABOUT.md
├── PLAN.md
├── PLAN_EXPANDED.md
├── README.md                  # Quick-start for operator
├── .env.example               # Template for secrets
├── config.py                  # Loads .env, exposes typed Config object
├── requirements.txt
├── run.py                     # CLI entry point: python run.py --topic "..."
├── agents/
│   ├── base.py                # BaseAgent abstract class
│   ├── topic_selection.py     # TopicSelectionAgent
│   ├── market_analysis.py     # MarketAnalysisAgent
│   ├── survey.py              # SurveyAgent
│   ├── research.py            # ResearchAgent
│   ├── data_collection.py     # DataCollectionAgent
│   ├── editing.py             # EditingAgent
│   ├── design.py              # DesignAgent
│   ├── publishing.py          # PublishingAgent
│   ├── marketing.py           # MarketingAgent
│   └── feedback.py            # FeedbackAgent
├── orchestrator/
│   ├── runner.py              # Main workflow runner
│   ├── workflow.py            # Workflow definition (DAG)
│   └── gates.py               # Human-in-the-loop gate logic
├── db/
│   ├── models.py              # Peewee ORM models
│   └── migrations/
├── templates/
│   └── report.html            # Jinja2 HTML template for PDF rendering
├── tests/
│   ├── test_agents.py
│   └── test_orchestrator.py
└── logs/
```

---

## BASE AGENT CONTRACT
File: `agents/base.py`

```python
from abc import ABC, abstractmethod
from typing import TypedDict
import logging

class AgentInput(TypedDict):
    job_id: str
    payload: dict  # Agent-specific payload

class AgentOutput(TypedDict):
    job_id: str
    status: str        # "success" | "needs_retry" | "needs_human" | "failed"
    payload: dict      # Agent-specific output
    error: str | None  # Populated only on failure

class BaseAgent(ABC):
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def run(self, input: AgentInput) -> AgentOutput:
        """
        Must be idempotent. Must not raise — return status="failed" instead.
        Must log entry and exit.
        """
        pass

    def _retry_api_call(self, fn, *args, max_retries=3, **kwargs):
        """Exponential backoff wrapper for any external API call."""
        import time
        for attempt in range(max_retries):
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                wait = 2 ** attempt
                self.logger.warning(f"Attempt {attempt+1} failed: {e}. Retrying in {wait}s")
                time.sleep(wait)
```

---

## AGENT SPECIFICATIONS

### TopicSelectionAgent
**File**: `agents/topic_selection.py`
**Purpose**: Find 5–10 candidate report topics with evidence of demand and gap in quality coverage.

**Input payload**:
```python
{
    "category_hint": str,        # e.g. "Indian financial regulation" or "" for open search
    "exclude_topics": list[str], # Topics already published, don't repeat
    "max_topics": int            # Default 10
}
```

**Output payload**:
```python
{
    "topics": [
        {
            "title": str,          # Proposed report title
            "rationale": str,      # Why this topic has demand + gap
            "target_audience": str,# "policy researcher" | "indie investor" | "NGO" | "student"
            "estimated_price_inr": int,
            "search_keywords": list[str],  # Keywords operator can verify in Google Trends
            "difficulty": str      # "low" | "medium" | "high"
        }
    ]
}
```

**Implementation notes**:
- Use Claude with web_search tool to scan Google Trends, Reddit India (r/IndiaInvestments, r/UPSC), and LinkedIn pulse topics
- Scoring criteria for topic selection: (1) search volume > 500/month, (2) top results older than 18 months OR clearly low-quality, (3) can be written from public sources
- If `category_hint` is empty, default to: Indian regulatory changes, ecological/climate policy India, emerging market investing themes
- Return status="needs_human" after generating list — operator must approve before pipeline continues (Gate 1)

---

### MarketAnalysisAgent
**File**: `agents/market_analysis.py`
**Purpose**: Validate that a selected topic has a reachable paying audience.

**Input payload**:
```python
{
    "topic": str,
    "target_audience": str
}
```

**Output payload**:
```python
{
    "audience_size_estimate": str,   # "small <1000" | "medium 1k-10k" | "large >10k"
    "distribution_channels": list[str],  # e.g. ["r/IndiaInvestments", "LinkedIn finance groups"]
    "willingness_to_pay": str,       # "low <500" | "medium 500-1500" | "high >1500"
    "competitor_reports": list[dict],# {title, url, price, quality_score 1-5}
    "recommendation": str            # "proceed" | "pivot" | "abandon"
}
```

**Implementation notes**:
- Use Claude with web_search to find existing paid reports on the topic (Gumroad search, Substack, SSRN)
- If 3+ high-quality free reports exist → recommend "pivot"
- If no paid reports found and topic is India-specific → strong signal to proceed

---

### ResearchAgent
**File**: `agents/research.py`
**Purpose**: Generate the full research report draft (10–15 pages) using Claude.

**Input payload**:
```python
{
    "topic": str,
    "target_audience": str,
    "supplementary_data": list[dict],  # From DataCollectionAgent if pre-run
    "report_structure": list[str] | None  # Optional override of section order
}
```

**Output payload**:
```python
{
    "report_markdown": str,    # Full report in markdown, ~3000-5000 words
    "word_count": int,
    "sections": list[str],     # Section headings found
    "citations": list[dict],   # {title, url, accessed_date}
    "quality_flags": list[str] # Any detected issues: "missing_data", "speculative_claim", etc.
}
```

**Implementation notes**:
- System prompt to Claude must include:
  - "You are a professional research analyst writing for [target_audience]"
  - "Cite every factual claim with a source URL"
  - "Use Indian context and INR where relevant"
  - "Do not fabricate statistics — if data is unavailable, say so explicitly"
  - "Minimum word count: 3000 words"
- Default report structure: Executive Summary → Context & Background → Key Findings (3–5 subsections) → Data Analysis → Implications → Recommendations → References
- Enable web_search tool on the Claude API call
- If word_count < 2500 after generation → set status="needs_retry" with note "draft too short"
- Return status="needs_human" after generation — operator reviews draft (Gate 2)

**Critical**: Set `max_tokens=8000` for this API call. Use `claude-sonnet-4-20250514`.

---

### DataCollectionAgent
**File**: `agents/data_collection.py`
**Purpose**: Gather structured supplementary data (tables, statistics) to enrich the research report.

**Input payload**:
```python
{
    "topic": str,
    "data_needs": list[str]  # e.g. ["GDP growth table 2019-2024", "RBI repo rate history"]
}
```

**Output payload**:
```python
{
    "datasets": [
        {
            "label": str,
            "data": str,       # Markdown table or structured text
            "source_url": str,
            "retrieved_at": str  # ISO datetime
        }
    ]
}
```

**Implementation notes**:
- Use Claude with web_search to retrieve tables from RBI, MOSPI, World Bank, MCA21
- For each data need, do one targeted search and extract the structured data
- Store raw retrieved content alongside cleaned version for audit trail

---

### EditingAgent
**File**: `agents/editing.py`
**Purpose**: Improve the draft for clarity, accuracy, tone, and formatting consistency.

**Input payload**:
```python
{
    "report_markdown": str,
    "target_audience": str,
    "quality_flags": list[str]  # Passed from ResearchAgent
}
```

**Output payload**:
```python
{
    "edited_markdown": str,
    "changes_summary": str,  # Brief description of what was changed
    "readability_score": str  # "poor" | "acceptable" | "good" | "excellent"
}
```

**Implementation notes**:
- Editing prompt to Claude must include:
  - Fix grammar and awkward phrasing
  - Ensure every section heading is clear
  - Ensure Executive Summary is standalone-readable (can be read without the rest)
  - Flag any remaining speculative claims not backed by citation
  - Do not change factual content — only improve expression
- If any quality_flags contain "speculative_claim" → add a disclaimer section to the report

---

### DesignAgent
**File**: `agents/design.py`
**Purpose**: Convert the edited markdown report into a professional PDF.

**Input payload**:
```python
{
    "edited_markdown": str,
    "report_title": str,
    "target_audience": str,
    "price_inr": int
}
```

**Output payload**:
```python
{
    "pdf_path": str,       # Absolute path to generated PDF file
    "page_count": int,
    "file_size_bytes": int
}
```

**Implementation notes**:
- Use Jinja2 to render `templates/report.html` with the markdown content (convert markdown → HTML first using `mistune`)
- Use `weasyprint` to convert HTML → PDF
- Template must include: JDHP cover page with title/date, page numbers, footer with "© JDHP", citation list at end
- Font: embed Google Font "Inter" or fallback to system sans-serif
- Color scheme: white background, dark navy headings (#1a2744), gray body text
- If page_count < 8 → log warning but don't block pipeline (operator saw the draft at Gate 2)
- PDF filename format: `JDHP_{snake_case_title}_{YYYYMMDD}.pdf`

---

### PublishingAgent
**File**: `agents/publishing.py`
**Purpose**: Upload the PDF to Gumroad and create a product listing.

**Input payload**:
```python
{
    "pdf_path": str,
    "report_title": str,
    "description_markdown": str,  # Generated by EditingAgent or operator-provided
    "price_inr": int,
    "tags": list[str]
}
```

**Output payload**:
```python
{
    "gumroad_product_id": str,
    "gumroad_url": str,
    "published_at": str  # ISO datetime
}
```

**Implementation notes**:
- Use Gumroad API v2: `POST https://api.gumroad.com/v2/products`
- Auth: Bearer token from `config.GUMROAD_ACCESS_TOKEN`
- Set `published: false` initially → operator confirms at Gate 3 before setting `published: true`
- Price must be set in USD (convert from INR using fixed rate or live rate via exchangerate-api.com)
- Description should include: what the report covers, who it's for, word count, date of research

---

### MarketingAgent
**File**: `agents/marketing.py`
**Purpose**: Generate ready-to-post promotional content for distribution channels.

**Input payload**:
```python
{
    "report_title": str,
    "gumroad_url": str,
    "description_markdown": str,
    "target_audience": str,
    "price_inr": int
}
```

**Output payload**:
```python
{
    "linkedin_post": str,      # 150-200 words, professional tone
    "reddit_post": dict,       # {subreddit, title, body} — informational, not spammy
    "twitter_thread": list[str], # 5-7 tweets
    "email_subject": str,
    "email_body": str
}
```

**Implementation notes**:
- LinkedIn post must NOT sound like an ad — lead with a key insight from the report
- Reddit post must follow subreddit rules: no direct sales pitch in body; link in comments only
- Suggested subreddits by audience: r/IndiaInvestments, r/UPSC, r/india, r/econindia
- All content generated by Claude with audience-appropriate tone
- Operator pastes/posts these manually in v1 (no auto-posting to social platforms)

---

### FeedbackAgent
**File**: `agents/feedback.py`
**Purpose**: Collect and synthesize buyer feedback to improve future reports.

**Input payload**:
```python
{
    "gumroad_product_id": str,
    "days_since_publish": int
}
```

**Output payload**:
```python
{
    "sale_count": int,
    "revenue_inr": float,
    "reviews": list[dict],          # {rating, comment, date}
    "avg_rating": float | None,
    "improvement_suggestions": list[str],  # Synthesized by Claude from reviews
    "next_topic_hints": list[str]   # Topics buyers asked about
}
```

**Implementation notes**:
- Use Gumroad API: `GET https://api.gumroad.com/v2/sales?product_id={id}`
- If sale_count == 0 after 7 days → trigger MarketAnalysisAgent re-run for that topic
- Synthesize reviews using Claude: "Given these reviews, what are the top 3 improvements and what related topics did buyers mention?"
- Feed `next_topic_hints` back into TopicSelectionAgent's next run

---

## ORCHESTRATOR

### runner.py
```python
# Core loop pseudocode — implement this exactly:

def run_pipeline(topic: str, category: str = ""):
    job_id = create_job(topic)
    
    # Stage 1: Topic validation
    topic_output = TopicSelectionAgent.run({job_id, category_hint: category})
    if topic_output.status == "needs_human":
        pause_and_notify(job_id, gate=1, data=topic_output.payload)
        # Execution resumes when operator calls: python run.py --resume JOB_ID --approve
        return
    
    # Stage 2: Market validation  
    market_output = MarketAnalysisAgent.run({job_id, topic})
    if market_output.payload["recommendation"] == "abandon":
        mark_job_abandoned(job_id)
        return

    # Stage 3: Research (with optional data pre-fetch)
    data_output = DataCollectionAgent.run({job_id, topic})
    research_output = ResearchAgent.run({job_id, topic, supplementary_data: data_output})
    if research_output.status == "needs_human":
        pause_and_notify(job_id, gate=2, data=research_output.payload)
        return

    # Stage 4: Edit → Design → Publish (Gate 3 before publish)
    edit_output = EditingAgent.run({job_id, research_output.payload})
    design_output = DesignAgent.run({job_id, edit_output.payload})
    pause_and_notify(job_id, gate=3, data=design_output.payload)
    # Operator reviews PDF, then: python run.py --resume JOB_ID --approve
```

### gates.py
- Gate notifications: print to console + write to `logs/gates.log`
- In v1 no email/SMS — operator watches terminal or checks log
- Resume command: `python run.py --resume <JOB_ID> --approve` or `--reject --reason "..."`

---

## DATABASE MODELS (db/models.py)

```python
# Using peewee ORM with SQLite

class Job(Model):
    id = UUIDField(primary_key=True)
    topic = TextField()
    status = CharField()  # "running"|"paused_gate_N"|"completed"|"abandoned"|"failed"
    created_at = DateTimeField()
    updated_at = DateTimeField()

class AgentRun(Model):
    id = UUIDField(primary_key=True)
    job = ForeignKeyField(Job)
    agent_name = CharField()
    input_payload = TextField()   # JSON string
    output_payload = TextField()  # JSON string
    status = CharField()
    started_at = DateTimeField()
    finished_at = DateTimeField()
    error = TextField(null=True)
```

---

## CONFIG (config.py)
```python
# All keys read from .env — never hardcoded
ANTHROPIC_API_KEY: str
GUMROAD_ACCESS_TOKEN: str
EXCHANGERATE_API_KEY: str  # For INR→USD conversion
LOG_LEVEL: str = "INFO"
DB_PATH: str = "jdhp.db"
OUTPUT_DIR: str = "output/"   # Where PDFs are saved
```

---

## TESTING REQUIREMENTS
- Every agent must have a unit test with a mocked API call
- Use `pytest` and `unittest.mock`
- Test: happy path, API failure (retry logic), empty response handling
- Integration test: run full pipeline on topic "Test Report Topic" with all API calls mocked
- CI: `pytest tests/` must pass before any commit

---

## KNOWN CONSTRAINTS AND GOTCHAS
1. **Gumroad API rate limit**: 500 requests/hour. Add sleep(0.1) between bulk calls.
2. **WeasyPrint on Linux**: requires `libcairo2`, `libpango-1.0-0`. Add to deployment docs.
3. **Claude token limits**: Research report generation may approach 8k output tokens. If truncated, split into sections and concatenate.
4. **INR pricing on Gumroad**: Gumroad does not support INR natively. Set price in USD, display INR equivalent in description.
5. **Reddit rate limits**: Do not auto-post. Human posts the MarketingAgent output manually.
6. **Idempotency**: If a job is re-run from a gate, skip already-completed agent stages by checking AgentRun table.

