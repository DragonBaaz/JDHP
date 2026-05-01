import re
from agents.base import BaseAgent, AgentInput, AgentOutput

class ResearchAgent(BaseAgent):
    def run(self, input: AgentInput) -> AgentOutput:
        """
        Generate full research report draft (3000-5000 words).
        Uses Claude Sonnet with up to 6 DuckDuckGo search rounds + mid-run compression.

        Claude's large context window and strong instruction-following means it
        will synthesise a high-quality report even when individual sources are thin —
        it cross-references, extrapolates from adjacent data, and flags uncertainty
        explicitly rather than simply giving up.
        """
        self.logger.info(f"Starting ResearchAgent for job {input['job_id']}")

        try:
            topic = input['payload'].get('topic', '')
            target_audience = input['payload'].get('target_audience', 'general audience')
            supplementary_data = input['payload'].get('supplementary_data', [])

            data_section = ""
            if supplementary_data:
                data_section = "\n\nSUPPLEMENTARY DATA (pre-fetched — incorporate and cite these):\n"
                for d in supplementary_data:
                    data_section += (
                        f"\n### {d.get('label', '')}\n"
                        f"Source: {d.get('source_url', 'N/A')}\n"
                        f"{d.get('data', '')}\n"
                    )

            system = (
                "You are a senior research analyst at an Indian policy and finance publishing house. "
                "Your job is to produce professional, deeply researched reports that practitioners "
                "actually pay for. Use search_web — run at least 5 targeted searches covering "
                "background, regulations, statistics, case studies, and recent news. "
                "If a source has only partial data, note that and triangulate from related sources. "
                "Never refuse to write the report because data is limited — synthesise what exists, "
                "clearly label data gaps, and make evidence-based projections where appropriate. "
                "Every factual claim must cite a real URL in parentheses."
            )

            prompt = f"""Write a comprehensive research report on: {topic}
Target audience: {target_audience}
{data_section}

STEP 1 — RESEARCH (run ALL these searches before writing):
1. "{topic} India 2024 2025" — get recent news and developments
2. "{topic} regulations policy India" — regulatory and legal context
3. "{topic} statistics data India" — quantitative evidence
4. "{topic} case studies examples" — real-world illustrations
5. "{topic} challenges opportunities India" — balanced perspectives
6. "{topic} expert analysis report" — analyst/researcher views
7. Any other searches you judge necessary to fill gaps

STEP 2 — WRITE THE REPORT using EXACTLY these headings:

## Executive Summary
(250-300 words. Fully self-contained — a busy reader should get the whole story from this section alone. Include 3 key findings and 2 key recommendations.)

## Background & Context
(Explain the topic's history, why it matters now, and the Indian regulatory/policy environment. Cite sources.)

## Key Findings
(5-7 numbered findings with evidence. Each finding = 1-2 sentences + supporting data/citation.)

## Data & Evidence
(Tables, statistics, comparisons. Use markdown tables where possible. Cite all figures with URLs.)

## Implications for {target_audience}
(Practical so-what for this specific audience. What should they do differently based on this research?)

## Recommendations
(5 specific, actionable recommendations numbered 1-5.)

## References
(List all cited URLs as a numbered list.)

REPORT RULES:
- Minimum 3000 words, target 4500 words
- Every factual claim followed by source URL in parentheses: (https://...)
- Use INR for currency, India-specific data where available
- If exact India data is unavailable, note it and cite the closest available data
- Do NOT truncate — write the complete report in full

Write the complete report now:"""

            # 6 rounds (was 8) — rounds 7-8 were hitting rate limits and causing retries.
            # compress_after_round=3 collapses accumulated search history at the midpoint,
            # preventing unbounded context growth that was the #1 cost driver.
            report_markdown = self._call_with_search(
                prompt, system=system, max_tokens=7000,
                max_search_rounds=6, compress_after_round=3
            )

            word_count = len(report_markdown.split())

            if word_count < 1500:
                self.logger.warning(f"Draft too short ({word_count} words), triggering retry.")
                return AgentOutput(
                    job_id=input['job_id'], status="needs_retry",
                    payload={"word_count": word_count},
                    error=f"Draft only {word_count} words (need 1500+). Claude may need another attempt."
                )

            urls = re.findall(r'https?://[^\s)>\]"\']+', report_markdown)
            citations = [{"url": u} for u in sorted(set(urls))]

            quality_flags = []
            if word_count < 3000:
                quality_flags.append(f"short_draft ({word_count} words, target 3000+)")
            if len(citations) < 5:
                quality_flags.append(f"few_citations ({len(citations)} URLs found, add more)")

            self.logger.info(f"Draft complete: {word_count} words, {len(citations)} citations")
            return AgentOutput(
                job_id=input['job_id'], status="needs_human",
                payload={
                    "report_markdown": report_markdown,
                    "word_count": word_count,
                    "citations": citations,
                    "quality_flags": quality_flags,
                },
                error=None
            )

        except Exception as e:
            self.logger.error(f"ResearchAgent failed: {e}", exc_info=True)
            return AgentOutput(job_id=input['job_id'], status="failed", payload={}, error=str(e))
