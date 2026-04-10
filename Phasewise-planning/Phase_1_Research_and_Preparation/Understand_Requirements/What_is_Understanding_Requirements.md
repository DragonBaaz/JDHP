# Understanding Requirements

## What This Step Means in JDHP Context
Before writing code, every contributor must read and internalize:
1. `ABOUT.md` — business model and non-goals
2. `PLAN.md` — revenue math and pipeline overview
3. `PLAN_EXPANDED.md` — full agent specs and coding contracts

## Checklist
- [ ] Can you name all 10 agents and their purpose from memory?
- [ ] Do you understand what a "Gate" is and when execution pauses?
- [ ] Do you understand the `AgentInput` / `AgentOutput` TypedDict contract?
- [ ] Do you understand why idempotency matters (hint: operator may re-run from any gate)?

## Agent Dependency Map
```
TopicSelectionAgent
    └── MarketAnalysisAgent
            └── SurveyAgent (fallback)
DataCollectionAgent (can run in parallel with MarketAnalysisAgent)
ResearchAgent (depends on: TopicSelectionAgent output + DataCollectionAgent output)
    └── EditingAgent
            └── DesignAgent
                    └── PublishingAgent
                            └── MarketingAgent
FeedbackAgent (runs independently after 7 days)
```

## Key Constraint
**Zero upfront infra cost.** Do not propose Docker, Kubernetes, Redis, or RabbitMQ for v1. SQLite + local Python is the entire stack.
