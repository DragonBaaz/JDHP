# Phase 1: Research and Preparation

## Goal
Set up the development environment and make all tool/technology decisions before writing a single line of agent code.

## Duration
Week 1–2

## Deliverables
- [ ] `.env.example` created with all required keys documented
- [ ] `requirements.txt` pinned with exact versions
- [ ] `config.py` working and tested
- [ ] SQLite DB initialised (`python db/models.py --init`)
- [ ] All API keys obtained and smoke-tested (Anthropic, Gumroad, ExchangeRate)
- [ ] `PLAN_EXPANDED.md` read and understood by all contributors

## Entry Condition
None — this is the start phase.

## Exit Condition
Running `python -c "from config import Config; c = Config(); print(c.ANTHROPIC_API_KEY[:8])"` prints the first 8 characters of your key without error.

## Failure Mode
If any API key cannot be obtained, do not proceed to Phase 2. Document the blocker in `logs/blockers.md`.
