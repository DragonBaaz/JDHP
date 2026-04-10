# Phase 2: System Design

## Goal
Define the exact interface contracts between all agents before implementing any of them. Code that matches the contracts in PLAN_EXPANDED.md will integrate without surprises.

## Duration
Week 2–3

## Deliverables
- [ ] `agents/base.py` implemented and tested
- [ ] `db/models.py` implemented, migration runs cleanly
- [ ] `orchestrator/workflow.py` PIPELINE_STAGES dict defined
- [ ] `config.py` loading from .env correctly
- [ ] All 10 agent files exist as stubs (class + `run()` returning hardcoded mock output)
- [ ] `python run.py --topic "test"` runs through the stub pipeline without error

## Why Stubs First
Build all agent stubs that return hardcoded `{"status": "success", "payload": {}}` before implementing any real logic. This lets you verify the orchestrator wiring is correct before adding API calls.

## Exit Condition
`python run.py --topic "test topic"` completes all stages with stubs and writes a completed job to the SQLite DB.
