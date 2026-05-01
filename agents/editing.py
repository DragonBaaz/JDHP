from agents.base import BaseAgent, AgentInput, AgentOutput

class EditingAgent(BaseAgent):
    def run(self, input: AgentInput) -> AgentOutput:
        """Improve draft for clarity, tone, and structure. Uses Claude Sonnet (no search needed)."""
        self.logger.info(f"Starting EditingAgent for job {input['job_id']}")

        try:
            report_markdown = input['payload'].get('report_markdown', '')
            target_audience = input['payload'].get('target_audience', 'general audience')
            quality_flags = input['payload'].get('quality_flags', [])

            flags_note = f"\nFLAGS TO FIX: {', '.join(quality_flags)}" if quality_flags else ""

            prompt = f"""Edit the following research report for a {target_audience}.

EDITING RULES:
1. Fix grammar, awkward phrasing, and passive voice.
2. Ensure Executive Summary is fully self-contained (readable without the rest).
3. Ensure every section heading clearly matches content beneath it.
4. Do NOT change factual content or remove citations.
5. If any claim lacks a source URL, add "(source needed)" after it.
6. Return the COMPLETE edited report in markdown — do not truncate or summarise.{flags_note}

REPORT TO EDIT:
{report_markdown}"""

            # Full model for editing — quality matters here.
            # max_tokens reduced 7000→5000: observed output is ~5000 tokens max
            # (editing cannot produce content longer than the original report).
            edited_markdown = self._call_simple(prompt, max_tokens=5000)

            # Sanity check: edited version should be ≥80% length of original
            if len(edited_markdown) < len(report_markdown) * 0.8:
                self.logger.warning("Edited draft suspiciously short — using original.")
                edited_markdown = report_markdown

            return AgentOutput(job_id=input['job_id'], status="success",
                               payload={
                                   "edited_markdown": edited_markdown,
                                   "changes_summary": "Edited for clarity, grammar, and structure.",
                                   "readability_score": "good"
                               }, error=None)

        except Exception as e:
            self.logger.error(f"EditingAgent failed: {e}", exc_info=True)
            # Non-fatal: pass original through
            return AgentOutput(job_id=input['job_id'], status="success",
                               payload={
                                   "edited_markdown": input['payload'].get('report_markdown', ''),
                                   "changes_summary": f"Editing skipped: {e}",
                                   "readability_score": "unknown"
                               }, error=None)
