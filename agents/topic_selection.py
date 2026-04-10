import json
from agents.base import BaseAgent, AgentInput, AgentOutput

class TopicSelectionAgent(BaseAgent):
    def run(self, input: AgentInput) -> AgentOutput:
        """Find 5 candidate report topics using GPT-4o + DuckDuckGo. Triggers Gate 1."""
        self.logger.info(f"Starting TopicSelectionAgent for job {input['job_id']}")

        try:
            category_hint = input['payload'].get('category_hint', 'Indian regulatory and financial changes')
            exclude_topics = input['payload'].get('exclude_topics', [])
            max_topics = input['payload'].get('max_topics', 5)

            system = (
                "You are a research market analyst for an Indian publishing house. "
                "Use the search_web tool to find trending topics with demand gaps. "
                "Search for: recent Indian regulatory changes, underserved research niches, "
                "topics where existing content is outdated or low quality."
            )

            prompt = f"""Find {max_topics} viable paid research report topics that meet ALL criteria:
1. High search demand in India (>500 searches/month estimated)
2. Existing content is outdated (>18 months old) OR clearly low-quality
3. Researchable from public sources
4. Relevant to: policy researchers, indie investors, NGOs, or government officials

Category focus: {category_hint}
Topics to exclude: {exclude_topics}

Search for evidence of demand and content gaps, then provide your final answer.

Respond ONLY with a JSON array. No preamble, no markdown fences. Each object must have:
"title", "rationale", "target_audience", "estimated_price_inr" (int),
"search_keywords" (array of 3 strings), "difficulty" ("low"|"medium"|"high")"""

            raw = self._call_with_search(prompt, system=system, max_tokens=2000)

            # Strip markdown fences if model added them
            raw = raw.strip()
            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0].strip()
            elif "```" in raw:
                raw = raw.split("```")[1].split("```")[0].strip()
            # Find the JSON array
            start = raw.find("[")
            end = raw.rfind("]") + 1
            if start != -1 and end > start:
                raw = raw[start:end]

            topics = json.loads(raw)

            return AgentOutput(job_id=input['job_id'], status="needs_human",
                               payload={"topics": topics}, error=None)

        except Exception as e:
            self.logger.error(f"TopicSelectionAgent failed: {e}", exc_info=True)
            return AgentOutput(job_id=input['job_id'], status="failed", payload={}, error=str(e))
