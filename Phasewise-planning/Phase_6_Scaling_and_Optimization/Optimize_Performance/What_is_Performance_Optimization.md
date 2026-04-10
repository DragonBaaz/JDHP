# Performance Optimization (Post-Launch)

## Only Optimize Based on Measured Pain
Do not optimize prematurely. Run the system for 30 days first, then identify the actual bottleneck.

## Likely Bottlenecks (in order of probability)
1. **ResearchAgent is slow** — Claude API call with web_search takes 30–60 seconds. Solution: Add progress indicator in CLI. Do not try to speed up the LLM.
2. **WeasyPrint PDF generation is slow on 1GB RAM VPS** — Solution: Generate PDF locally, transfer to VPS for hosting only.
3. **Too many topics generating, too few selling** — Solution: Tighten TopicSelectionAgent scoring criteria.

## Metrics to Track (add to FeedbackAgent)
- Time from `run.py` invocation to Gate 3 approval request
- Conversion rate: page views → sales per report
- Revenue per operator-hour (gates only)

## When to Consider Upgrading Stack
Only if monthly revenue > ₹50,000 AND bottleneck is clearly infrastructure (not content quality or distribution).
