# Setting Up Data Pipelines

## Data Pipeline in JDHP
Not a streaming pipeline — a simple sequential fetch pattern:

1. DataCollectionAgent identifies 3–5 specific data needs based on the topic
2. For each need, it calls Claude with web_search to retrieve and format the data
3. Results stored in `AgentRun.output_payload` (JSON) for ResearchAgent to consume

## Implementation Pattern
```python
# In DataCollectionAgent.run()
data_needs = self._identify_data_needs(topic)  # Ask Claude what data would strengthen this report
datasets = []
for need in data_needs:
    data = self._fetch_data(need)  # Claude + web_search call
    datasets.append(data)
return {"status": "success", "payload": {"datasets": datasets}}
```

## Data Security
- No PII collected
- All data from public sources (government sites, RBI, World Bank)
- Data stored in SQLite only (not transmitted externally except to Anthropic API)
