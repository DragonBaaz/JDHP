# Impact Evaluation

## Monthly Review Checklist
Run this checklist on the first day of each month:

1. **Revenue**: Total INR collected via Gumroad last 30 days
2. **Volume**: Number of reports published
3. **Conversion**: Best and worst performing reports (views → sales ratio)
4. **Quality**: Average rating across all reports
5. **Topics**: Which topic categories sell best (use to bias TopicSelectionAgent)
6. **Time cost**: Actual operator hours spent at gates

## Decision Rules
- If avg rating < 3.5 → EditingAgent prompt needs improvement before next batch
- If conversion < 1% → TopicSelectionAgent criteria need tightening (better gap detection)
- If revenue < ₹10k after 60 days → reassess pricing or distribution channels
- If revenue > ₹50k → begin Phase 6 scaling discussions

## Feedback Loop Implementation
FeedbackAgent's `next_topic_hints` should be automatically surfaced in the next TopicSelectionAgent run. Implement this in `orchestrator/runner.py`:

```python
# At start of TopicSelectionAgent run, load previous feedback hints
previous_hints = load_feedback_hints_from_db()  # SELECT from AgentRun where agent_name='FeedbackAgent'
input_payload["category_hint"] += f"\nPrevious buyer topic requests: {previous_hints}"
```
