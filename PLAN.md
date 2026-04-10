# JDHP Master Plan

## Business Model in One Sentence
Use Claude to generate differentiated 10–15 page research reports on underserved niche topics, sell them on Gumroad at ₹500–2000, repeat at volume.

## Revenue Math
- Target: ₹30,000/month break-even
- At ₹1000 avg price → need 30 sales/month
- At 2% conversion from page views → need 1500 page views/month
- With 10 active reports → each needs ~150 views/month (achievable via SEO + Reddit/LinkedIn distribution)

## The Agent Pipeline (v1 Scope)
```
[TopicSelectionAgent] → [ResearchAgent] → [EditingAgent] → [DesignAgent] → [PublishingAgent]
         ↑                                                                          ↓
[MarketAnalysisAgent] ←←←←←←←←←←←←←←← [FeedbackAgent] ←←←←←←←←←←←←←←←←←←←←←←←
```

Each arrow is a JSON payload passed between agents. The orchestrator manages retries and gate approvals.

## Human-in-the-Loop Gates
The system pauses and notifies the operator at:
1. **Gate 1** — After TopicSelectionAgent: approve/reject topic list
2. **Gate 2** — After ResearchAgent: approve/reject draft before editing
3. **Gate 3** — After DesignAgent: approve PDF before publish
4. **Gate 4** — After 7 days live: review sales + FeedbackAgent output

## Differentiation Strategy
Target reports where:
- Top 3 Google results are >2 years old, OR
- Topic is India-specific and English-language analysis is thin, OR
- Requires synthesis across 5+ sources (too much work for a casual reader)

Examples: "SEBI AIF Category III Tax Treatment 2024", "Carbon Credit Markets for Indian Farmers", "PLI Scheme ROI by Sector"

## Full Agent Roster
See `PLAN_EXPANDED.md` for detailed agent specs.

## Phased Delivery
- **Phase 1** (Week 1–2): Setup, tooling decisions, repo scaffold
- **Phase 2** (Week 2–3): System design, agent contracts defined
- **Phase 3** (Week 3–5): MVP — Topic → Research → Publish pipeline working
- **Phase 4** (Week 5–8): Full agent roster, dashboard, orchestration
- **Phase 5** (Week 8–9): Deployment, soft launch
- **Phase 6** (Ongoing): Scale, optimize, expand topics
- **Phase 7** (Ongoing): Continuous improvement loop

See `PLAN_EXPANDED.md` for phase-by-phase implementation detail.
