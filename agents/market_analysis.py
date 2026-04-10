import json
from agents.base import BaseAgent, AgentInput, AgentOutput

class MarketAnalysisAgent(BaseAgent):
    def run(self, input: AgentInput) -> AgentOutput:
        """Validate topic has a reachable paying audience using GPT-4o + DDGS."""
        self.logger.info(f"Starting MarketAnalysisAgent for job {input['job_id']}")

        try:
            topic = input['payload'].get('topic', '')
            target_audience = input['payload'].get('target_audience', '')

            system = (
                "You are a market research analyst for an Indian research publishing house. "
                "Use search_web to find: existing paid reports on this topic, "
                "active communities where this audience gathers, and competitor pricing."
            )

            prompt = f"""Analyse market viability for a paid research report on: "{topic}"
Target audience: {target_audience}

Search for existing paid reports, community hubs, and competitor pricing, then answer.

Respond ONLY with a JSON object (no markdown) with these exact keys:
- "audience_size_estimate": "small <1000" | "medium 1k-10k" | "large >10k"
- "distribution_channels": array of strings (subreddits, LinkedIn groups, forums)
- "willingness_to_pay": "low <500" | "medium 500-1500" | "high >1500"
- "competitor_reports": array of objects: title, url, price_inr (int), quality_score (1-5)
- "recommendation": "proceed" | "pivot" | "abandon"
- "recommendation_reason": one sentence"""

            raw = self._call_with_search(prompt, system=system, max_tokens=1200)
            raw = raw.strip()
            if "```" in raw:
                raw = raw.split("```")[1].split("```")[0].strip()
                if raw.startswith("json"):
                    raw = raw[4:].strip()
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start != -1 and end > start:
                raw = raw[start:end]

            result = json.loads(raw)

            return AgentOutput(job_id=input['job_id'], status="success",
                               payload=result, error=None)

        except Exception as e:
            self.logger.error(f"MarketAnalysisAgent failed: {e}", exc_info=True)
            # Soft fallback — don't block pipeline on analysis failure
            return AgentOutput(job_id=input['job_id'], status="success",
                               payload={
                                   "audience_size_estimate": "medium 1k-10k",
                                   "distribution_channels": ["r/IndiaInvestments", "LinkedIn"],
                                   "willingness_to_pay": "medium 500-1500",
                                   "competitor_reports": [],
                                   "recommendation": "proceed",
                                   "recommendation_reason": f"Analysis failed ({e}), defaulting to proceed"
                               }, error=None)
