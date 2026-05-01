"""
topic_selection.py — Find 5 viable paid report topics using Claude + DuckDuckGo.
Triggers Gate 1 (human selects one topic).
"""
import json
from agents.base import BaseAgent, AgentInput, AgentOutput

class TopicSelectionAgent(BaseAgent):
    def run(self, input: AgentInput) -> AgentOutput:
        """Find 5 candidate report topics. Triggers Gate 1."""
        self.logger.info(f"Starting TopicSelectionAgent for job {input['job_id']}")

        try:
            category_hint = input['payload'].get('category_hint', 'Indian regulatory and financial changes')
            exclude_topics = input['payload'].get('exclude_topics', [])
            max_topics = input['payload'].get('max_topics', 5)

            system = (
                "You are a market analyst for an Indian research publishing house that sells "
                "paid PDF reports (₹500-2000) to policy researchers, indie investors, NGOs, "
                "and government officials. Your job is to find topics where: (a) demand is high "
                "but good content is scarce or outdated, and (b) the audience has demonstrated "
                "willingness to pay for research. Search thoroughly before deciding."
            )

            prompt = f"""Find {max_topics} viable paid research report topics.

CRITERIA (all must be met):
1. Indian audience with >500 estimated monthly searches on this topic
2. Existing free content is outdated (>18 months) OR clearly low-quality/superficial
3. Topic is fully researchable from public sources
4. Target audience: policy researchers, investors, NGOs, or government officials

CATEGORY FOCUS: {category_hint}
EXCLUDE THESE TOPICS: {exclude_topics if exclude_topics else "none"}

SEARCH STRATEGY — run these searches:
- "[category] India 2024 2025 policy changes" — find recent regulatory shifts
- "[category] India research report demand" — find what people are searching for
- "[category] site:reddit.com OR site:quora.com" — find questions people are asking
- "[category] India gaps underserved niche" — find content gaps
- Run 2-3 more searches to validate demand for your top candidates

After searching, respond ONLY with a JSON array (no preamble, no markdown fences).
Each object must have exactly these keys:
- "title": string — clear, specific report title
- "rationale": string — why this topic has demand and a content gap (1-2 sentences)
- "target_audience": string — specific audience segment
- "estimated_price_inr": integer — suggested price (500-2000)
- "search_keywords": array of 3 strings — best search terms buyers would use
- "difficulty": "low" | "medium" | "high" — research difficulty"""

            # 4 rounds sufficient: prompt defines 4 explicit search strategies
            raw = self._call_with_search(prompt, system=system, max_tokens=2500, max_search_rounds=4)

            # Strip markdown fences if Claude added them
            raw = raw.strip()
            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0].strip()
            elif "```" in raw:
                raw = raw.split("```")[1].split("```")[0].strip()
            start = raw.find("[")
            end = raw.rfind("]") + 1
            if start != -1 and end > start:
                raw = raw[start:end]

            try:
                topics = json.loads(raw)
            except json.JSONDecodeError as e:
                self.logger.warning(f"JSON parse failed (will retry): {e}\nRaw: {raw[:500]}")
                return AgentOutput(
                    job_id=input['job_id'], status="needs_retry",
                    payload={"raw_response": raw[:1000]},
                    error=f"JSON parse error: {e}"
                )

            if not isinstance(topics, list) or len(topics) == 0:
                return AgentOutput(
                    job_id=input['job_id'], status="needs_retry",
                    payload={"raw_response": raw[:1000]},
                    error="Response is not a non-empty JSON array"
                )

            required_fields = ["title", "rationale", "target_audience", "estimated_price_inr"]
            for i, t in enumerate(topics):
                missing = [f for f in required_fields if f not in t]
                if missing:
                    return AgentOutput(
                        job_id=input['job_id'], status="needs_retry",
                        payload={"partial_topics": topics},
                        error=f"Topic {i} missing required fields: {missing}"
                    )

            self.logger.info(f"Generated {len(topics)} topics successfully")
            return AgentOutput(
                job_id=input['job_id'], status="needs_human",
                payload={"topics": topics},
                error=None
            )

        except Exception as e:
            self.logger.error(f"TopicSelectionAgent failed: {e}", exc_info=True)
            return AgentOutput(job_id=input['job_id'], status="failed", payload={}, error=str(e))
