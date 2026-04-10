# Agent Roles Quick Reference

| Agent | One-line Role | Triggers Human Gate? |
|---|---|---|
| TopicSelectionAgent | Find 5–10 viable report topics | Yes (Gate 1) |
| MarketAnalysisAgent | Validate audience + competition for a topic | No |
| SurveyAgent | Gather audience preference data (v2 feature) | No |
| DataCollectionAgent | Pull structured data/tables for the report | No |
| ResearchAgent | Generate full 3000–5000 word report draft | Yes (Gate 2) |
| EditingAgent | Improve clarity, fix flags, ensure citations | No |
| DesignAgent | Render markdown → professional PDF | No |
| PublishingAgent | Upload PDF to Gumroad (unpublished until Gate 3) | Yes (Gate 3) |
| MarketingAgent | Generate LinkedIn/Reddit/Twitter content | No |
| FeedbackAgent | Analyse sales + reviews after 7 days | No |

## v1 Scope
Agents marked "v2 feature" (SurveyAgent) should have a stub implementation that returns a hardcoded "no survey data available" output rather than being left unimplemented. The orchestrator must not break if SurveyAgent returns empty data.
