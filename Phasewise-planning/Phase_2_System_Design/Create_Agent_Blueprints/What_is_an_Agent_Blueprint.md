# Agent Blueprint

## What Every Agent Must Have
Each file in `agents/` must implement:

```python
class XxxAgent(BaseAgent):
    """
    One-line description of what this agent does.
    
    Input payload keys: (list them)
    Output payload keys: (list them)
    External APIs called: (list them, or "none")
    Gate triggered: (Gate N, or "none")
    """
    
    def run(self, input: AgentInput) -> AgentOutput:
        self.logger.info(f"Starting {self.__class__.__name__} for job {input['job_id']}")
        try:
            # ... implementation ...
            result = self._do_work(input["payload"])
            self.logger.info(f"Completed {self.__class__.__name__} successfully")
            return {"job_id": input["job_id"], "status": "success", "payload": result, "error": None}
        except Exception as e:
            self.logger.error(f"{self.__class__.__name__} failed: {e}", exc_info=True)
            return {"job_id": input["job_id"], "status": "failed", "payload": {}, "error": str(e)}
```

## The Input/Output Loop Contract
Each agent's docstring must specify its "loop condition" — what causes it to return `status="needs_retry"` vs `status="needs_human"` vs `status="failed"`:

- `needs_retry`: Transient issue, worth trying again (API timeout, empty LLM response)
- `needs_human`: Structural issue, operator decision required (draft too short, no good topics found)
- `failed`: Unrecoverable error (invalid API key, file write permission error)
