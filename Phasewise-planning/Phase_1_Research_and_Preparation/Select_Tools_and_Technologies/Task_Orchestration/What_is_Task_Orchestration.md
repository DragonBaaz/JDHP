# Task Orchestration in JDHP

## Chosen Approach
Custom lightweight runner in `orchestrator/runner.py`. No external orchestration framework.

## Why Not Airflow/Celery
- Airflow requires a web server, scheduler, and database — massive overhead for a solo operator
- Celery requires Redis or RabbitMQ — adds infra cost and complexity
- For 1–3 concurrent jobs, a simple loop with SQLite state is sufficient

## How the Runner Works
1. Operator runs: `python run.py --topic "Carbon credits for Indian farmers"`
2. Runner creates a Job record in SQLite with status="running"
3. Runner calls agents in sequence as defined in `PIPELINE_STAGES`
4. At each Gate, runner sets job status="paused_gate_N" and exits
5. Operator reviews, then runs: `python run.py --resume <JOB_ID> --approve`
6. Runner loads job from DB, skips completed stages, continues from gate

## Trigger Conditions for Agent Retry
- Agent returns `status="needs_retry"` → runner waits 30 seconds and retries (max 3 times)
- Agent returns `status="needs_human"` → runner pauses at gate
- Agent returns `status="failed"` → runner marks job failed, logs error, stops
