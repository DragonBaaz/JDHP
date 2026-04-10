# Scalability Plan

## v1 Scale Target
- 1 operator
- 1–3 concurrent reports
- 10–30 reports published per month
- Single VPS or local machine

## v1 Does NOT Need
- Horizontal scaling
- Load balancers
- Distributed queues
- Container orchestration

## What Enables Future Scale (Design Decisions Made Now)
1. **Stateless agents** — all state in DB means you can run multiple workers later
2. **job_id threading** — every DB record tied to a job_id means parallel jobs don't collide
3. **Config-driven pipeline** — PIPELINE_STAGES dict means you can add agents without changing runner logic
4. **PDF to disk** — storing PDFs in OUTPUT_DIR (not in DB) means easy migration to S3 later

## When to Scale (Trigger Conditions)
Consider moving to a hosted DB + worker queue only when:
- Monthly reports > 100, OR
- Multiple human operators running simultaneous jobs, OR
- Pipeline takes >30 min per report and operator is blocked

Until then: SQLite + single process is correct.
