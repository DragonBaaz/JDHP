# Selecting Tools and Technologies

## Decision Already Made
See `ABOUT.md` Technology Decisions table. These are FIXED for v1. Do not re-evaluate during implementation.

## Why Not [Popular Alternative]?
- **LangChain / LlamaIndex**: Adds abstraction that hides what's happening; debugging harder; not needed for 10 well-defined agents
- **FastAPI/Flask**: No web server needed in v1; CLI is sufficient
- **PostgreSQL**: SQLite is adequate for one operator running <10 concurrent jobs
- **Docker**: Adds setup friction; install instructions in README are sufficient

## Setup Commands (copy-paste ready)
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install anthropic peewee python-dotenv weasyprint mistune jinja2 requests pytest
pip freeze > requirements.txt
```

## API Keys Needed
| Service | Where to Get | Env Var Name |
|---|---|---|
| Anthropic | console.anthropic.com | ANTHROPIC_API_KEY |
| Gumroad | app.gumroad.com/settings/advanced | GUMROAD_ACCESS_TOKEN |
| ExchangeRate | exchangerate-api.com (free tier) | EXCHANGERATE_API_KEY |
