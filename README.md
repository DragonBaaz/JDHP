# JDHP — Agentic Publishing House

AI-augmented research reports, automated from topic selection to Gumroad listing.

## What It Does
Takes a topic category as input, runs a 10-agent pipeline to generate a professional PDF research report, and creates a Gumroad product listing — with human approval at 3 gates.

## System Requirements
- Python 3.11+
- Linux/macOS (Windows untested)
- System libraries for PDF generation:
  ```bash
  sudo apt-get install -y libcairo2 libpango-1.0-0 libgdk-pixbuf2.0-0 libffi-dev
  ```

## Setup
```bash
python3.11 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env       # Then edit .env with your API keys
python db/models.py --init # Initialize SQLite database
```

## Run a Report
```bash
# Start a new report pipeline
python run.py --topic "Carbon credit markets for Indian farmers 2025"

# Resume after a gate (approve or reject)
python run.py --resume <JOB_ID> --approve
python run.py --resume <JOB_ID> --reject --reason "topic too broad"

# Check all job statuses
python run.py --dashboard

# Run feedback collection on a published report (after 7 days)
python run.py --feedback --job-id <JOB_ID>
```

## Gates (Human Approval Points)
| Gate | When | What to Review |
|---|---|---|
| Gate 1 | After TopicSelectionAgent | Approve/reject topic candidates |
| Gate 2 | After ResearchAgent | Review draft quality before editing |
| Gate 3 | After DesignAgent | Approve PDF before Gumroad publish |

## Architecture
See `PLAN_EXPANDED.md` for complete agent specs and coding contracts.
