# AI Framework: Anthropic Claude

## Chosen Framework
**Anthropic Python SDK** (`pip install anthropic`)

## Why Claude over GPT for JDHP
- Larger context window handles full 5000-word report + editing in one call
- Web search tool built-in (no separate SerpAPI subscription needed)
- Better instruction-following for structured output (TypedDict contracts)

## How to Call Claude in JDHP
```python
import anthropic

client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

response = client.messages.create(
    model="claude-sonnet-4-20250514",  # Always use this model
    max_tokens=8000,                    # Set 8000 for ResearchAgent, 2000 for others
    tools=[{"type": "web_search_20250305", "name": "web_search"}],  # Only when needed
    messages=[
        {"role": "user", "content": prompt}
    ]
)

# Extract text from response
text = " ".join(
    block.text for block in response.content if block.type == "text"
)
```

## When to Enable web_search Tool
- TopicSelectionAgent: YES (needs trend data)
- MarketAnalysisAgent: YES (needs competitor research)
- DataCollectionAgent: YES (needs live statistics)
- ResearchAgent: YES (needs citations)
- EditingAgent: NO (works on existing text only)
- DesignAgent: NO (no API call needed)
- PublishingAgent: NO
- MarketingAgent: NO
- FeedbackAgent: NO

## Cost Estimate
- ResearchAgent: ~8000 output tokens × $0.003/1k ≈ $0.024 per report
- Total pipeline (all agents): ~$0.05–0.10 per report
- At ₹1000 avg price → API cost is <1% of revenue
