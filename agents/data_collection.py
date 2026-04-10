import json
from datetime import datetime
from agents.base import BaseAgent, AgentInput, AgentOutput

class DataCollectionAgent(BaseAgent):
    def run(self, input: AgentInput) -> AgentOutput:
        """Gather structured supplementary data using GPT-4o + DDGS."""
        self.logger.info(f"Starting DataCollectionAgent for job {input['job_id']}")

        try:
            topic = input['payload'].get('topic', '')
            data_needs = input['payload'].get('data_needs', [])

            # If no explicit data needs, ask GPT-4o-mini what data would strengthen this report
            if not data_needs:
                needs_raw = self._call_simple(
                    f'For a research report on "{topic}" targeting Indian readers, '
                    f'list 3 specific data needs (statistics or tables that would strengthen it). '
                    f'Respond ONLY as a JSON array of short strings.',
                    use_mini=True, max_tokens=200
                ).strip().strip("```json").strip("```").strip()
                start = needs_raw.find("[")
                end = needs_raw.rfind("]") + 1
                if start != -1 and end > start:
                    needs_raw = needs_raw[start:end]
                try:
                    data_needs = json.loads(needs_raw)
                except Exception:
                    data_needs = [f"Key statistics for {topic} India 2024"]

            datasets = []
            for need in data_needs[:3]:  # Cap at 3 to respect rate limits
                system = "You are a data researcher. Use search_web to find the requested data."
                prompt = (
                    f'Find current data for: "{need}" in the context of "{topic}" (India focus).\n'
                    f'Return:\n'
                    f'Line 1: The source URL\n'
                    f'Lines 2+: The data as a markdown table or structured text'
                )

                text = self._call_with_search(prompt, system=system, max_tokens=600,
                                              max_search_rounds=2)
                lines = text.strip().split('\n')
                source_url = next((l.strip() for l in lines if l.strip().startswith('http')), "")
                data_text = '\n'.join(
                    l for l in lines if not l.strip().startswith('http')
                ).strip()

                datasets.append({
                    "label": need,
                    "data": data_text,
                    "source_url": source_url,
                    "retrieved_at": datetime.utcnow().isoformat()
                })

            return AgentOutput(job_id=input['job_id'], status="success",
                               payload={"datasets": datasets}, error=None)

        except Exception as e:
            self.logger.error(f"DataCollectionAgent failed: {e}", exc_info=True)
            # Non-fatal — ResearchAgent works without supplementary data
            return AgentOutput(job_id=input['job_id'], status="success",
                               payload={"datasets": []}, error=None)
