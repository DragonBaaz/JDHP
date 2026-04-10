# Agent Dependencies

## Dependency Rules
1. An agent may only be called when all its upstream agents have status="success" in the `AgentRun` table for the current job_id
2. The orchestrator is responsible for enforcing this — agents themselves do NOT check dependencies
3. Dependencies are defined in `orchestrator/workflow.py` as an ordered list, not hardcoded in agents

## Dependency Table
```python
# orchestrator/workflow.py — define exactly this dict
PIPELINE_STAGES = [
    {"agent": "TopicSelectionAgent",  "depends_on": []},
    {"agent": "MarketAnalysisAgent",  "depends_on": ["TopicSelectionAgent"]},
    {"agent": "DataCollectionAgent",  "depends_on": ["MarketAnalysisAgent"]},
    {"agent": "ResearchAgent",        "depends_on": ["DataCollectionAgent"]},
    {"agent": "EditingAgent",         "depends_on": ["ResearchAgent"]},
    {"agent": "DesignAgent",          "depends_on": ["EditingAgent"]},
    {"agent": "PublishingAgent",      "depends_on": ["DesignAgent"]},
    {"agent": "MarketingAgent",       "depends_on": ["PublishingAgent"]},
    # FeedbackAgent runs on a schedule, not in the main pipeline
]
```

## Parallelism Note
In v1, all stages run sequentially. Do not implement parallel execution. The architecture supports it in future (DataCollectionAgent can theoretically run alongside MarketAnalysisAgent) but the added complexity is not worth it for a solo operator running 1–3 reports at a time.
