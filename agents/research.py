import re
from agents.base import BaseAgent, AgentInput, AgentOutput

class ResearchAgent(BaseAgent):
    def run(self, input: AgentInput) -> AgentOutput:
        """
        Generate full research report draft (3000-5000 words).
        Uses GPT-4o with multiple DDGS search rounds. Triggers Gate 2.

        Note on GitHub Models rate limits: this agent makes the heaviest API use.
        It may take 2-4 minutes. If you hit rate limits, wait 1 minute and resume.
        """
        self.logger.info(f"Starting ResearchAgent for job {input['job_id']}")

        try:
            topic = input['payload'].get('topic', '')
            target_audience = input['payload'].get('target_audience', 'general audience')
            supplementary_data = input['payload'].get('supplementary_data', [])

            data_section = ""
            if supplementary_data:
                data_section = "\n\nSUPPLEMENTARY DATA (already retrieved, incorporate this):\n"
                for d in supplementary_data:
                    data_section += (
                        f"\n{d.get('label', '')} (source: {d.get('source_url', '')}):\n"
                        f"{d.get('data', '')}\n"
                    )

            system = (
                "You are a professional research analyst writing for an Indian audience. "
                "Use the search_web tool multiple times to gather current data, "
                "regulations, statistics, and expert opinions before writing the report. "
                "Every factual claim in the final report must cite a real URL."
            )

            prompt = f"""Write a comprehensive research report on: {topic}
Target audience: {target_audience}
{data_section}

RESEARCH INSTRUCTIONS:
1. First, search for background, regulatory context, and recent developments
2. Search for data, statistics, and case studies relevant to India
3. Search for expert opinions or analyses on this topic
4. Then write the complete report

REPORT RULES:
- Every factual claim followed by source URL in parentheses
- Use Indian context, INR currency, India-specific regulations
- Minimum 3000 words, target 4500 words
- Use EXACTLY these section headings:
  ## Executive Summary
  ## Background & Context
  ## Key Findings
  ## Data & Evidence
  ## Implications for {target_audience}
  ## Recommendations
  ## References

Write the complete report now."""

            # Allow up to 5 search rounds for thorough research
            report_markdown = self._call_with_search(
                prompt, system=system, max_tokens=6000, max_search_rounds=5
            )

            word_count = len(report_markdown.split())

            if word_count < 2000:
                self.logger.warning(f"Draft too short ({word_count} words), triggering retry.")
                return AgentOutput(job_id=input['job_id'], status="needs_retry",
                                   payload={"word_count": word_count},
                                   error=f"Draft only {word_count} words, need 2000+")

            urls = re.findall(r'https?://[^\s)>\]]+', report_markdown)
            citations = [{"url": u} for u in sorted(set(urls))]

            return AgentOutput(job_id=input['job_id'], status="needs_human",
                               payload={
                                   "report_markdown": report_markdown,
                                   "word_count": word_count,
                                   "citations": citations,
                                   "quality_flags": []
                               }, error=None)

        except Exception as e:
            self.logger.error(f"ResearchAgent failed: {e}", exc_info=True)
            return AgentOutput(job_id=input['job_id'], status="failed", payload={}, error=str(e))
