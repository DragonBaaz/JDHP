# FeedbackAgent Implementation Guide

## File
`agents/feedback.py`

## Schedule
Run via cron or manual trigger: `python run.py --feedback --job-id <JOB_ID>`
NOT part of the main pipeline. Runs 7 days after publish.

## Gumroad Sales API
```python
def get_sales(self, product_id):
    resp = requests.get(
        "https://api.gumroad.com/v2/sales",
        headers={"Authorization": f"Bearer {self.config.GUMROAD_ACCESS_TOKEN}"},
        params={"product_id": product_id}
    )
    return resp.json()["sales"]
```

## Feedback Synthesis Prompt
```python
SYNTHESIS_PROMPT = """
Given these customer reviews for a research report, extract:
1. Top 3 specific improvements readers wanted
2. Related topics readers mentioned wanting to read about next
3. Overall sentiment (positive/neutral/negative)

Reviews:
{reviews_text}

Respond in JSON format only.
"""
```

## Action Rules
- sale_count == 0 after 7 days → log warning, suggest running MarketingAgent again
- avg_rating < 3.0 → log warning, flag for manual review
- next_topic_hints → save to DB, surface in next TopicSelectionAgent run
