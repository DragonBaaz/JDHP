# Dashboard Implementation

## Library
Use `rich` Python library. No web framework.

## Implementation
```python
# orchestrator/dashboard.py
from rich.console import Console
from rich.table import Table
from db.models import Job, AgentRun

def show_dashboard():
    console = Console()
    table = Table(title="JDHP Job Status")
    table.add_column("Job ID", style="cyan")
    table.add_column("Topic", style="white")
    table.add_column("Status", style="green")
    table.add_column("Current Stage", style="yellow")
    table.add_column("Revenue (INR)", style="magenta")
    
    for job in Job.select().order_by(Job.created_at.desc()).limit(20):
        last_run = AgentRun.select().where(AgentRun.job == job).order_by(AgentRun.started_at.desc()).first()
        table.add_row(
            str(job.id)[:8],
            job.topic[:40],
            job.status,
            last_run.agent_name if last_run else "—",
            str(job.revenue_inr or "—")
        )
    
    console.print(table)
```

## Manual Override
The dashboard does not need real-time refresh in v1. Running `python run.py --dashboard` prints the current state and exits. This is sufficient.
