# What Is The Plan (Summary for Coding Models)

## One Paragraph Summary
JDHP is a Python CLI tool that takes a research topic as input and outputs a published Gumroad product listing. It does this via a chain of 10 AI agents, each calling the Anthropic Claude API. Human approval is required at 3 gates. The entire state of a job is stored in SQLite. The tool is designed to be run by a single operator on a laptop or cheap VPS.

## What "Production Quality" Means Here
- No unhandled exceptions anywhere — all exceptions caught, logged, returned as `status="failed"`
- All external calls retried 3 times with exponential backoff
- All agent inputs/outputs serialised to DB so a job can be resumed after crash
- PDF output is professional-looking (cover page, page numbers, citations)
- Gumroad listing is unpublished until operator explicitly approves (Gate 3)
- Marketing content is informational-first, not spammy

## What "Production Quality" Does NOT Mean Here
- 99.9% uptime SLA
- Multi-user authentication
- Test coverage >80% (aim for happy path + one failure mode per agent)
- Containerization
