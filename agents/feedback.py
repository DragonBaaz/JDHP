import json
import requests
from agents.base import BaseAgent, AgentInput, AgentOutput

class FeedbackAgent(BaseAgent):
    def run(self, input: AgentInput) -> AgentOutput:
        """Pull real sales from Gumroad and synthesise buyer feedback with GPT-4o-mini."""
        self.logger.info(f"Starting FeedbackAgent for job {input['job_id']}")

        try:
            product_id = input['payload'].get('gumroad_product_id', '')
            days_since_publish = input['payload'].get('days_since_publish', 7)

            def _get_sales():
                resp = requests.get(
                    "https://api.gumroad.com/v2/sales",
                    headers={"Authorization": f"Bearer {self.config.GUMROAD_ACCESS_TOKEN}"},
                    params={"product_id": product_id},
                    timeout=15
                )
                resp.raise_for_status()
                return resp.json().get("sales", [])

            sales = self._retry_api_call(_get_sales)
            sale_count = len(sales)
            revenue_usd = sum(float(s.get("price", 0)) / 100 for s in sales)
            revenue_inr = round(revenue_usd * 84, 2)

            reviews = [
                {"rating": s.get("rating"), "comment": s.get("review_message", ""),
                 "date": s.get("created_at", "")}
                for s in sales if s.get("review_message")
            ]
            avg_rating = (
                sum(r["rating"] for r in reviews if r["rating"]) / len(reviews)
            ) if reviews else None

            improvement_suggestions = []
            next_topic_hints = []

            if reviews:
                reviews_text = "\n".join(
                    f"Rating: {r['rating']}/5 — {r['comment']}" for r in reviews
                )
                synth_prompt = f"""Given these buyer reviews for a research report:
{reviews_text}

Extract:
1. Top 3 specific improvements readers want
2. Related topics buyers mentioned wanting next

Respond ONLY with JSON: {{"improvements": [...], "next_topics": [...]}}"""

                raw = self._call_simple(synth_prompt, max_tokens=400, use_mini=True)
                raw = raw.strip().strip("```json").strip("```").strip()
                start = raw.find("{")
                end = raw.rfind("}") + 1
                if start != -1 and end > start:
                    raw = raw[start:end]
                parsed = json.loads(raw)
                improvement_suggestions = parsed.get("improvements", [])
                next_topic_hints = parsed.get("next_topics", [])

            if sale_count == 0 and days_since_publish >= 7:
                self.logger.warning("Zero sales after 7 days — consider re-running MarketingAgent.")

            return AgentOutput(job_id=input['job_id'], status="success",
                               payload={
                                   "sale_count": sale_count,
                                   "revenue_inr": revenue_inr,
                                   "reviews": reviews,
                                   "avg_rating": avg_rating,
                                   "improvement_suggestions": improvement_suggestions,
                                   "next_topic_hints": next_topic_hints
                               }, error=None)

        except Exception as e:
            self.logger.error(f"FeedbackAgent failed: {e}", exc_info=True)
            return AgentOutput(job_id=input['job_id'], status="failed", payload={}, error=str(e))
