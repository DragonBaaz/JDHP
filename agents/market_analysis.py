"""
market_analysis.py — Validate topic has a reachable paying audience.
Uses Claude + DuckDuckGo. Soft fallback on failure (non-blocking).
"""
import json
from agents.base import BaseAgent, AgentInput, AgentOutput

class MarketAnalysisAgent(BaseAgent):
    def run(self, input: AgentInput) -> AgentOutput:
        """Validate audience and pricing viability using Claude + DDGS."""
        self.logger.info(f"Starting MarketAnalysisAgent for job {input['job_id']}")

        try:
            topic = input['payload'].get('topic', '')
            target_audience = input['payload'].get('target_audience', '')

            system = (
                "You are a market research analyst. Search for evidence of actual demand: "
                "paid reports that exist on this topic, active communities discussing it, "
                "and what prices competitors charge. Be specific — vague answers are useless."
            )

            prompt = f"""Analyse market viability for a paid research report on: "{topic}"
Target audience: {target_audience}

SEARCHES TO RUN:
1. '"{topic}" filetype:pdf OR "buy report" India' — find existing paid reports
2. '"{topic}" site:reddit.com India' — find community discussion
3. '"{topic}" site:linkedin.com group OR community' — find LinkedIn groups
4. '"{topic}" India market research price' — find competitor pricing

After searching, respond ONLY with a JSON object (no markdown, no extra text):
{{
  "audience_size_estimate": "small <1000" | "medium 1k-10k" | "large >10k",
  "distribution_channels": ["list of specific subreddits, LinkedIn groups, forums found"],
  "willingness_to_pay": "low <500" | "medium 500-1500" | "high >1500",
  "competitor_reports": [
    {{"title": "...", "url": "...", "price_inr": 0, "quality_score": 3}}
  ],
  "recommendation": "proceed" | "pivot" | "abandon",
  "recommendation_reason": "one specific sentence with evidence"
}}"""

            # Haiku is sufficient for pattern-matching + JSON output (saves ~44% vs Sonnet)
            raw = self._call_with_search(prompt, system=system, max_tokens=1500,
                                         max_search_rounds=4, model=self.MODEL_MINI)
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
            return AgentOutput(job_id=input['job_id'], status="success", payload=result, error=None)

        except Exception as e:
            self.logger.error(f"MarketAnalysisAgent failed: {e}", exc_info=True)
            # Soft fallback — don't block the pipeline on analysis failure
            return AgentOutput(
                job_id=input['job_id'], status="success",
                payload={
                    "audience_size_estimate": "medium 1k-10k",
                    "distribution_channels": ["r/IndiaInvestments", "r/india", "LinkedIn"],
                    "willingness_to_pay": "medium 500-1500",
                    "competitor_reports": [],
                    "recommendation": "proceed",
                    "recommendation_reason": f"Analysis failed ({e}), defaulting to proceed."
                },
                error=None
            )
