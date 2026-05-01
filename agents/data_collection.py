"""
data_collection.py — Gather structured supplementary data for the ResearchAgent.
Uses Claude + DuckDuckGo. Non-blocking on failure (ResearchAgent works without it).

Optimisation: all 3 data needs are batched into ONE _call_with_search() session
instead of 3 separate sessions. This cuts from up to 9 tool loops → 4, reducing
DataCollectionAgent cost by ~51%.
"""
import re
import json
from datetime import datetime
from agents.base import BaseAgent, AgentInput, AgentOutput

class DataCollectionAgent(BaseAgent):
    def run(self, input: AgentInput) -> AgentOutput:
        """Gather structured supplementary data using Claude + DDGS (batched)."""
        self.logger.info(f"Starting DataCollectionAgent for job {input['job_id']}")

        try:
            topic = input['payload'].get('topic', '')
            data_needs = input['payload'].get('data_needs', [])

            # Ask Haiku to identify 3 specific data needs if none provided
            if not data_needs:
                needs_raw = self._call_simple(
                    f'For a research report on "{topic}" targeting Indian readers, '
                    f'list exactly 3 specific data needs (statistics, tables, or figures '
                    f'that would make the report credible and useful). '
                    f'Respond ONLY as a JSON array of short, specific strings. '
                    f'Example: ["SEBI AIF registration count 2023-24", '
                    f'"Average gig worker income India 2022-24"]',
                    use_mini=True, max_tokens=300
                ).strip()
                if "```" in needs_raw:
                    needs_raw = needs_raw.split("```")[1].split("```")[0].strip()
                    if needs_raw.startswith("json"):
                        needs_raw = needs_raw[4:].strip()
                start = needs_raw.find("[")
                end = needs_raw.rfind("]") + 1
                if start != -1 and end > start:
                    needs_raw = needs_raw[start:end]
                try:
                    data_needs = json.loads(needs_raw)
                except Exception:
                    data_needs = [
                        f"Key statistics for {topic} India 2024",
                        f"Market size or growth data for {topic} India",
                        f"Regulatory timeline for {topic} India",
                    ]

            data_needs = data_needs[:3]
            self.logger.info(f"Data needs identified: {data_needs}")

            # ── Single batched search session for all 3 needs ────────────────
            # Previous: 3 separate _call_with_search() calls (9 total tool loops)
            # Now: 1 call handles all 3 (4 tool loops max) → ~51% cost reduction

            needs_formatted = "\n".join(
                f"{i+1}. {need}" for i, need in enumerate(data_needs)
            )

            system = (
                "You are a data researcher for an Indian research publishing house. "
                "Use search_web to find specific data for each item requested. "
                "Run targeted searches — one per data need is usually sufficient. "
                "Always provide a source URL. If exact data is unavailable, find the "
                "closest proxy and label it clearly."
            )

            prompt = (
                f'Find current data for a research report on "{topic}" (India focus).\n\n'
                f'DATA NEEDS:\n{needs_formatted}\n\n'
                f'Search for each item, then respond in EXACTLY this format '
                f'(use the --- delimiters precisely):\n\n'
                f'---DATASET 1---\n'
                f'LABEL: [exact label from item 1]\n'
                f'SOURCE_URL: [full URL]\n'
                f'DATA:\n'
                f'[markdown table or bullet points]\n\n'
                f'---DATASET 2---\n'
                f'LABEL: [exact label from item 2]\n'
                f'SOURCE_URL: [full URL]\n'
                f'DATA:\n'
                f'[markdown table or bullet points]\n\n'
                f'---DATASET 3---\n'
                f'LABEL: [exact label from item 3]\n'
                f'SOURCE_URL: [full URL]\n'
                f'DATA:\n'
                f'[markdown table or bullet points]'
            )

            text = self._call_with_search(
                prompt, system=system, max_tokens=2000, max_search_rounds=4
            )

            # ── Parse the structured response ────────────────────────────────
            datasets = []
            blocks = re.split(r'---DATASET\s+\d+---', text)
            # blocks[0] is any text before the first delimiter — skip it
            data_blocks = blocks[1:4]

            for i, block in enumerate(data_blocks):
                label = data_needs[i] if i < len(data_needs) else f"Dataset {i+1}"
                source_url = ""
                data_lines = []
                in_data = False

                for line in block.strip().split('\n'):
                    stripped = line.strip()
                    if stripped.startswith("LABEL:"):
                        candidate = stripped.split("LABEL:", 1)[1].strip()
                        if candidate:
                            label = candidate
                    elif stripped.startswith("SOURCE_URL:"):
                        url_part = stripped.split("SOURCE_URL:", 1)[1].strip()
                        urls = re.findall(r'https?://\S+', url_part)
                        source_url = urls[0] if urls else url_part
                    elif stripped == "DATA:":
                        in_data = True
                    elif in_data:
                        data_lines.append(line)
                    elif stripped.startswith("http") and not source_url:
                        source_url = stripped

                data_text = '\n'.join(data_lines).strip() or "(data not found)"
                datasets.append({
                    "label": label,
                    "data": data_text,
                    "source_url": source_url,
                    "retrieved_at": datetime.utcnow().isoformat()
                })
                self.logger.info(
                    f"Dataset {i+1} collected: '{label}' "
                    f"(source: {source_url[:60] if source_url else 'unknown'})"
                )

            # Pad to 3 datasets if parsing found fewer blocks (fallback)
            while len(datasets) < len(data_needs):
                i = len(datasets)
                datasets.append({
                    "label": data_needs[i] if i < len(data_needs) else f"Dataset {i+1}",
                    "data": "(not found)",
                    "source_url": "",
                    "retrieved_at": datetime.utcnow().isoformat()
                })

            return AgentOutput(
                job_id=input['job_id'], status="success",
                payload={"datasets": datasets}, error=None
            )

        except Exception as e:
            self.logger.error(f"DataCollectionAgent failed: {e}", exc_info=True)
            # Non-fatal — ResearchAgent works without pre-fetched supplementary data
            return AgentOutput(
                job_id=input['job_id'], status="success",
                payload={"datasets": []}, error=None
            )
