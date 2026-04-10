# TopicSelectionAgent Implementation Guide

## File
`agents/topic_selection.py`

## Core Logic

### Prompt Strategy
```python
TOPIC_SELECTION_PROMPT = """
You are a research market analyst for an Indian publishing house.

Find {max_topics} viable report topics that meet ALL of these criteria:
1. High search demand in India (estimated >500 searches/month)
2. Existing content is outdated (>18 months old) OR clearly low-quality
3. Can be researched using publicly available sources
4. Relevant to at least one of: policy researchers, indie investors, NGOs, government officials

Topics to exclude (already published): {exclude_topics}
Category focus (or "open" if none): {category_hint}

For each topic, provide:
- Proposed report title
- Why demand exists (cite a trend, news event, or search pattern)
- Target audience
- Estimated price in INR (₹500/₹1000/₹1500/₹2000)
- 3 search keywords to verify demand
- Difficulty: low/medium/high

Format your response as a JSON array.
"""
```

### Parsing the Response
The LLM response should be JSON. Wrap the parse in try/except — if JSON fails, use regex to extract the array. Log the raw response before parsing to help debug malformed output.

### Gate 1 Behaviour
After generating topics, always return `status="needs_human"` with the full topic list in the payload. The operator will approve or reject individual topics via the CLI.

### CLI Gate 1 Interface (implement in gates.py)
```
Gate 1 — Topic Approval
-----------------------
Job ID: abc-123
Generated topics:
  [1] SEBI AIF Category III Tax Treatment 2025
  [2] Carbon Credit Markets for Indian Farmers  
  [3] PLI Scheme ROI by Sector Q4 2024

Enter topic numbers to approve (comma-separated), or 'all', or 'none':
> 1,3

Approved: [1] SEBI AIF Category III Tax Treatment 2025
Approved: [3] PLI Scheme ROI by Sector Q4 2024
```
