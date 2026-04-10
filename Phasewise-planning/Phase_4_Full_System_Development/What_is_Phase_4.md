# Phase 4: Full System Development

## Goal
Build all remaining agents, wire them into the orchestrator, and add the centralized dashboard.

## Duration
Week 5–8

## Deliverables
- [ ] All 10 agents implemented (not just MVP 4)
- [ ] EditingAgent polishes research drafts before PDF generation
- [ ] MarketAnalysisAgent validates topics before research begins
- [ ] DataCollectionAgent pre-fetches structured data for ResearchAgent
- [ ] MarketingAgent generates LinkedIn/Reddit/Twitter content after publish
- [ ] FeedbackAgent polls Gumroad sales after 7 days
- [ ] Dashboard (simple terminal UI using `rich` library — no web server)
- [ ] End-to-end test with real API calls on one real topic

## Dashboard Spec
Use the `rich` Python library (`pip install rich`) to build a terminal dashboard showing:
- All jobs and their current status
- Most recent agent run per job
- Gate status (pending/approved/rejected)
- Revenue total from FeedbackAgent data

Do NOT build a web UI dashboard. A rich terminal table is sufficient for v1.

## Exit Condition
Running `python run.py --dashboard` shows all jobs, and running the full pipeline on a real topic produces a publishable report with no manual intervention except the 3 gates.
