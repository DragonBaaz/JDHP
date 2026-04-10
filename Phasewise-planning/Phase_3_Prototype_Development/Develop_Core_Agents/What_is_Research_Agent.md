# ResearchAgent Implementation Guide

## File
`agents/research.py`

## Step-by-Step Implementation

### Step 1: Build the system prompt
```python
RESEARCH_SYSTEM_PROMPT = """
You are a professional research analyst. Your task is to write a comprehensive research report.

STRICT RULES:
1. Every factual claim must be followed by a source URL in parentheses
2. Do not fabricate statistics or data — if unavailable, say "data not available"
3. Use Indian context, INR currency, and India-specific regulations where relevant
4. Minimum 3000 words, target 4500 words
5. Structure the report with these exact sections:
   - Executive Summary (300 words max, standalone readable)
   - Background & Context
   - Key Findings (3-5 subsections)
   - Data & Evidence
   - Implications for [target_audience]
   - Recommendations
   - References (numbered list of all URLs cited)
"""
```

### Step 2: Build the user prompt
```python
def build_prompt(topic, target_audience, supplementary_data):
    data_section = ""
    if supplementary_data:
        data_section = "\n\nSUPPLEMENTARY DATA TO INCORPORATE:\n"
        for d in supplementary_data:
            data_section += f"\n{d['label']} (source: {d['source_url']}):\n{d['data']}\n"
    
    return f"""Write a research report on: {topic}
    
Target audience: {target_audience}
{data_section}

Begin with the Executive Summary section."""
```

### Step 3: Handle long output
If the response is under 2500 words, set `status="needs_retry"` with payload note "draft too short, retry with explicit word count reminder". The retry will add "IMPORTANT: Previous draft was too short. This draft MUST be at least 3000 words." to the prompt.

### Step 4: Parse citations
After generation, extract all URLs from the markdown using regex `https?://[^\s)]+` and populate the `citations` list in the output payload.
