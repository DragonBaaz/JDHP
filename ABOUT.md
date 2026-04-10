# JDHP — Agentic Publishing House

## Mission
Produce and sell AI-augmented research reports at volume: fast to generate, differentiated by depth, priced for the Indian research/investor/NGO market (₹500–2000 per report).

## Vision
A fully automated agentic pipeline where a human operator selects a topic category and the system handles everything from trend discovery to Gumroad listing — with human review gates at quality checkpoints.

## Core Business Logic
- **Revenue driver**: volume × conversion rate × average price
- **Differentiation**: reports exist in niches where Google returns low-quality or outdated results
- **Cost structure**: near-zero (API calls + hosting), margin is high
- **Solo-operator friendly**: burst-mode human involvement only at gates (topic approval, quality sign-off, pricing decision)

## What This Codebase Is
A Python-based multi-agent orchestration system. Each agent is a class with:
- a `run(input: dict) -> dict` interface
- a defined retry/fallback contract
- stateless execution (state lives in a central SQLite job store)

The orchestrator calls agents in sequence/parallel per workflow definition. No RabbitMQ or Kafka for v1 — use a simple SQLite-backed task queue to keep zero-infra startup cost.

## Technology Decisions (Fixed for v1)
| Concern | Choice | Reason |
|---|---|---|
| Language | Python 3.11+ | Ecosystem, LLM SDKs |
| AI backbone | Anthropic Claude (claude-sonnet-4-20250514) | Quality/cost ratio |
| Orchestration | Custom lightweight runner (see `orchestrator/`) | No Airflow overhead for solo operator |
| Job store | SQLite via `peewee` ORM | Zero infra, works locally and on cheap VPS |
| PDF generation | `weasyprint` + Jinja2 HTML templates | Programmatic, no InDesign |
| Publishing | Gumroad API | Direct integration, no manual upload |
| Deployment | Single VPS (DigitalOcean ₹700/mo droplet) or local cron | No Kubernetes for v1 |

## Non-Goals for v1
- Real-time streaming
- Multi-tenant SaaS
- LLM fine-tuning
- Video/audio reports
