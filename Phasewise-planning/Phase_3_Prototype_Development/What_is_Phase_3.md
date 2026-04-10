# Phase 3: Prototype Development (MVP)

## Goal
Build a working end-to-end pipeline for the 3 core agents: TopicSelectionAgent → ResearchAgent → PublishingAgent (unpublished draft). Skip all other agents. This proves the value chain works before building the full system.

## Duration
Week 3–5

## MVP Scope (what to build)
- TopicSelectionAgent with real Claude + web_search calls
- ResearchAgent with real Claude + web_search calls
- DesignAgent with real WeasyPrint PDF output
- PublishingAgent creating an UNPUBLISHED Gumroad product
- Gate 1 (topic approval) and Gate 3 (publish approval) working
- Orchestrator running these 4 agents in sequence

## MVP Excludes (defer to Phase 4)
- MarketAnalysisAgent, SurveyAgent, DataCollectionAgent, EditingAgent, MarketingAgent, FeedbackAgent
- Dashboard
- Marketing content generation

## Exit Condition (Definition of Done for Phase 3)
Running the following command produces a PDF file and an unpublished Gumroad draft listing:
```bash
python run.py --topic "SEBI Small and Medium REITs regulation 2024 India"
```
The PDF must be:
- At least 8 pages
- Have a cover page with the report title and date
- Have a references section with at least 5 URLs

## Known Risks
- WeasyPrint install on some systems requires `libcairo` system library — test this in Week 3
- Gumroad API may require account verification before API access — apply in Week 1
