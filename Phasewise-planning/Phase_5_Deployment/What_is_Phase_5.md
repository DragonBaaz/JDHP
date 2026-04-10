# Phase 5: Deployment

## Goal
Make the system runnable on a VPS or any Linux machine with a clean install.

## Duration
Week 8–9

## Deployment Target
DigitalOcean Basic Droplet ($6/month, 1GB RAM, Ubuntu 22.04) OR operator's local machine.

## System Dependencies (Linux)
```bash
sudo apt-get install -y python3.11 python3.11-venv libcairo2 libpango-1.0-0 libgdk-pixbuf2.0-0 libffi-dev
```
These are required by WeasyPrint. Document this in README.md.

## Deployment Steps
```bash
git clone <repo>
cd JDHP
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with real API keys
python db/models.py --init
python run.py --topic "test topic"  # Smoke test
```

## Soft Launch Definition
- Publish first 2 reports on Gumroad
- Post to 2 subreddits manually using MarketingAgent output
- Do NOT spend money on ads
- Wait 7 days, run FeedbackAgent, evaluate before publishing more

## README Requirements
README.md must include:
- What JDHP does (2 sentences)
- System requirements
- Setup commands (copy-paste ready)
- How to run a report end-to-end
- How to resume from a gate
- How to check job status
