# Agent Communication Design

## Communication Pattern
**Direct function calls via orchestrator** — not message queues.

In v1, agents do not communicate directly with each other. The orchestrator:
1. Calls Agent A
2. Receives Agent A's output dict
3. Transforms it into Agent B's input dict
4. Calls Agent B

This transformation logic lives in `orchestrator/runner.py` as explicit mapping functions.

## Payload Transformation Example
```python
# In runner.py — explicit, readable, no magic
def research_input_from_market_output(job_id, market_output, data_output):
    return {
        "job_id": job_id,
        "payload": {
            "topic": market_output["payload"]["topic"],
            "target_audience": market_output["payload"]["audience_size_estimate"],
            "supplementary_data": data_output["payload"]["datasets"],
            "report_structure": None  # Use default
        }
    }
```

## No Message Broker in v1
RabbitMQ and Kafka are listed in the original plan as options. **Do not implement them.** They add operational complexity (running a broker process, managing queues) that is not justified for a synchronous single-operator pipeline. The SQLite AgentRun table provides the same audit trail.
