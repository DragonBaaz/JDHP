# JDHP — Agentic Publishing House

> An end-to-end multi-agent pipeline that researches, writes, designs, and publishes professional PDF research reports — with human approval gates at every critical decision point.

---

## Overview

JDHP automates the full lifecycle of niche research report production. A single `python run.py --topic "..."` command triggers a coordinated pipeline of eight AI agents that collectively:

1. Discover viable report topics using live web search
2. Validate market demand and pricing
3. Collect real datasets and statistics
4. Write a 3,000–5,000 word research draft
5. Edit and polish the content
6. Render a professional PDF
7. Create a Gumroad product listing
8. Generate multi-channel marketing copy

Human operators retain control at **three approval gates** — topic selection, draft quality review, and pre-publish sign-off — making this a **human-in-the-loop agentic system**, not a black box.

---

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLI  (run.py)                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │   Orchestrator  │  SQLite job store (Peewee ORM)
                    └────────┬────────┘
                             │
         ┌───────────────────▼──────────────────────┐
         │                                          │
   ┌─────▼──────────┐                               │
   │ TopicSelection  │  ← DuckDuckGo + Claude       │
   │    Agent        │    Proposes 5 topic candidates│
   └─────┬──────────┘                               │
         │  ⚑  GATE 1 — Operator picks topic        │
   ┌─────▼──────────┐                               │
   │ MarketAnalysis  │  Validates demand & pricing   │
   └─────┬──────────┘                               │
   ┌─────▼──────────┐                               │
   │ DataCollection  │  Gathers 3 datasets (batched) │
   └─────┬──────────┘                               │
   ┌─────▼──────────┐                               │
   │  Research       │  3–5k word draft, 6 search    │
   │    Agent        │  rounds + context compression │
   └─────┬──────────┘                               │
         │  ⚑  GATE 2 — Operator reviews draft      │
   ┌─────▼──────────┐                               │
   │   Editing       │  Grammar, clarity, structure  │
   └─────┬──────────┘                               │
   ┌─────▼──────────┐                               │
   │   Design        │  Markdown → HTML → PDF        │
   │    Agent        │  (Jinja2 + weasyprint)        │
   └─────┬──────────┘                               │
   ┌─────▼──────────┐                               │
   │  Publishing     │  Gumroad draft listing        │
   │    Agent        │  INR → USD via ExchangeRate   │
   └─────┬──────────┘                               │
         │  ⚑  GATE 3 — Operator approves publish   │
   ┌─────▼──────────┐                               │
   │   Marketing     │  LinkedIn · Reddit · Twitter  │
   │    Agent        │  + email copy (Haiku model)   │
   └─────┬──────────┘                               │
         │  (7+ days later)                         │
   ┌─────▼──────────┐                               │
   │   Feedback      │  Sales + reviews → next hints │
   └─────────────────┘                               │
         │                                          │
         └──────────────────────────────────────────┘
```

---

## Key Features

- **Agentic orchestration** — eight stateless agents with a clean `run(input) → output` contract, coordinated by a lightweight custom runner
- **Human-in-the-loop gates** — operator approval required at topic selection, draft review, and pre-publish
- **Live web research** — DuckDuckGo integration with a 7-day SQLite search cache (zero repeat cost)
- **Context compression** — mid-run conversation compaction after search round 3 to stay within token limits on long research tasks
- **Cost-aware model routing** — Claude Sonnet for heavy reasoning, Claude Haiku for lightweight JSON tasks and marketing copy
- **Batched data collection** — all three dataset needs resolved in one LLM session (saves ~51% cost vs. sequential calls)
- **Professional PDF output** — A4-formatted PDF with cover page, typography, tables, and auto-numbered citations via weasyprint + Jinja2
- **Automated publishing** — Gumroad product creation with live INR→USD conversion, file upload, and post-gate publish trigger
- **Stateful job resumption** — any interrupted pipeline can be resumed from the last gate without re-running earlier agents
- **Feedback loop** — post-publication agent fetches sales data, reviews, and synthesises improvement suggestions

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| AI Backbone | Anthropic Claude API (`claude-sonnet-4-6`, `claude-haiku-4-5`) |
| Web Search | DuckDuckGo (`ddgs`) — no API key required |
| Job Store | SQLite via Peewee ORM |
| PDF Generation | weasyprint + Jinja2 + mistune |
| Publishing | Gumroad REST API |
| Currency | ExchangeRate API (free tier) |
| Terminal UI | Rich |
| Configuration | python-dotenv |

---

## System Requirements

- **Python 3.11+**
- **Linux / macOS** (Windows support is untested)
- System libraries for PDF generation:

```bash
# Ubuntu / Debian
sudo apt-get install -y libcairo2 libpango-1.0-0 libgdk-pixbuf2.0-0 libffi-dev
```

---

## Setup

```bash
# 1. Clone and enter the repo
git clone https://github.com/<your-username>/JDHP.git
cd JDHP

# 2. Create and activate a virtual environment
python3.11 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Open .env and fill in your API keys (see .env.example for all required keys)

# 5. Initialise the database
python run.py --init-db
```

### Required API Keys

| Variable | Where to get it |
|---|---|
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) |
| `GUMROAD_ACCESS_TOKEN` | Gumroad Settings → Advanced → Applications |
| `EXCHANGERATE_API_KEY` | [exchangerate-api.com](https://www.exchangerate-api.com) (free tier) |

---

## Usage

### Start a new pipeline

```bash
python run.py --topic "Carbon credit markets for Indian farmers 2025"
# Prints: Job ID: <job_id>  (save this for gate resumption)
```

### Gate 1 — Topic selection

The pipeline pauses after `TopicSelectionAgent` with 5 candidate topics. Review the output, then:

```bash
# Approve and select topic at index 2 (default is 0)
python run.py --resume <JOB_ID> --approve --topic-index 2

# Reject all candidates and abandon
python run.py --resume <JOB_ID> --reject --reason "topics too generic"
```

### Gate 2 — Draft quality review

The pipeline pauses after `ResearchAgent`. Review the draft in the job output, then:

```bash
python run.py --resume <JOB_ID> --approve
python run.py --resume <JOB_ID> --reject --reason "insufficient data on pricing"
```

### Gate 3 — Pre-publish approval

The pipeline pauses after `PublishingAgent` with a Gumroad draft listing created. Review the listing, then:

```bash
python run.py --resume <JOB_ID> --approve   # triggers live publish
python run.py --resume <JOB_ID> --reject --reason "price too high"
```

### Monitor all jobs

```bash
python run.py --dashboard
```

### Run post-publication feedback (after 7+ days)

```bash
python run.py --feedback --job-id <JOB_ID>
```

---

## Gate Summary

| Gate | Trigger Agent | What to Review | Approve Action |
|---|---|---|---|
| Gate 1 | `TopicSelectionAgent` | 5 topic candidates — viability, uniqueness, demand | Pick one with `--topic-index N` |
| Gate 2 | `ResearchAgent` | Draft quality, word count, citation quality | Proceed to editing + design |
| Gate 3 | `PublishingAgent` | Gumroad listing, price, PDF preview | Publish live to Gumroad |

---

## Job States

```
running → paused_TopicSelectionAgent → running → ... → paused_ResearchAgent
       → running → paused_PublishingAgent → running → completed
                                                    ↘ abandoned (on reject)
                                                    ↘ failed    (on error)
```

---

## Repository Structure

```
JDHP/
├── run.py                      # CLI entry point
├── config.py                   # Environment variable loader & validation
├── requirements.txt
├── .env.example                # API key template (copy to .env — never commit .env)
├── agents/
│   ├── base.py                 # Abstract BaseAgent: Claude calls, retry, search
│   ├── topic_selection.py      # Gate 1: discover 5 topic candidates
│   ├── market_analysis.py      # Validate demand and pricing
│   ├── data_collection.py      # Gather 3 datasets (batched)
│   ├── research.py             # Gate 2: 3–5k word draft
│   ├── editing.py              # Polish grammar and structure
│   ├── design.py               # Render PDF via weasyprint
│   ├── publishing.py           # Gate 3: Gumroad listing
│   ├── marketing.py            # Promotional copy (LinkedIn, Reddit, Twitter)
│   ├── feedback.py             # Post-sale feedback synthesis
│   └── search_tool.py          # DuckDuckGo wrapper with 7-day cache
├── orchestrator/
│   └── runner.py               # Agent sequencing, gate logic, job resumption
├── db/
│   └── models.py               # Peewee ORM: Job, AgentRun models
├── templates/
│   └── report.html             # Jinja2 HTML template for PDF rendering
├── output/                     # Generated PDFs (gitignored)
└── logs/                       # Pipeline logs (gitignored)
```

---

## Cost Optimisations

| Optimisation | Mechanism | Impact |
|---|---|---|
| Model routing | Haiku for marketing/JSON, Sonnet for research | ~60% cost reduction on lightweight tasks |
| Search caching | 7-day SQLite cache keyed by MD5(query) | Zero cost on repeated topics |
| Context compression | Collapse search history after round 3 | Prevents token overflow on long research runs |
| Batched data collection | All 3 dataset needs in one LLM session | ~51% cost reduction vs. sequential calls |
| Snippet truncation | Search results capped at 250 chars | ~62% token reduction per search result |

---

## Security

- API keys are loaded exclusively from environment variables — never hardcoded
- `.env` is listed in `.gitignore` and has never been committed to this repository
- Use `.env.example` as the template; populate `.env` locally and keep it out of version control

---

## License

This project is released for educational and portfolio purposes.
