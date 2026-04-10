from agents.base import BaseAgent, AgentInput, AgentOutput

class MarketingAgent(BaseAgent):
    def run(self, input: AgentInput) -> AgentOutput:
        """Generate insight-led promotional content. Uses GPT-4o-mini (no search needed)."""
        self.logger.info(f"Starting MarketingAgent for job {input['job_id']}")

        try:
            report_title = input['payload'].get('report_title', '')
            gumroad_url = input['payload'].get('gumroad_url', '')
            description = input['payload'].get('description_markdown', '')
            target_audience = input['payload'].get('target_audience', 'researchers')
            price_inr = input['payload'].get('price_inr', 1000)

            prompt = f"""Create promotional content for this research report. Lead with KEY INSIGHTS, not sales pitch.

Report title: {report_title}
Target audience: {target_audience}
Price: ₹{price_inr}
Gumroad link: {gumroad_url}
Report summary: {description[:500]}

Generate ALL sections below. Use exact labels shown.

LINKEDIN_POST:
(150-200 words, professional, open with surprising finding or stat, end with link)

REDDIT_TITLE:
(one line, informational, no "buy" language)

REDDIT_BODY:
(3-4 paragraphs of genuine insight; mention paid report only at end)

TWEET_1:
TWEET_2:
TWEET_3:
TWEET_4:
TWEET_5:
(5 tweets forming a thread; each under 280 chars; insight-first, link only in last tweet)

EMAIL_SUBJECT:
(one line)

EMAIL_BODY:
(100 words max, professional)"""

            text = self._call_simple(prompt, max_tokens=2000, use_mini=True)

            def _extract(label, after_labels):
                start = text.find(f"{label}:")
                if start == -1:
                    return ""
                start += len(label) + 1
                end = len(text)
                for al in after_labels:
                    pos = text.find(f"{al}:", start)
                    if pos != -1 and pos < end:
                        end = pos
                return text[start:end].strip()

            all_labels = ["LINKEDIN_POST", "REDDIT_TITLE", "REDDIT_BODY",
                          "TWEET_1", "TWEET_2", "TWEET_3", "TWEET_4", "TWEET_5",
                          "EMAIL_SUBJECT", "EMAIL_BODY"]

            tweets = [_extract(f"TWEET_{i}", all_labels) for i in range(1, 6)]
            tweets = [t for t in tweets if t]

            return AgentOutput(job_id=input['job_id'], status="success",
                               payload={
                                   "linkedin_post": _extract("LINKEDIN_POST", all_labels),
                                   "reddit_post": {
                                       "subreddit": "r/IndiaInvestments",
                                       "title": _extract("REDDIT_TITLE", all_labels),
                                       "body": _extract("REDDIT_BODY", all_labels)
                                   },
                                   "twitter_thread": tweets,
                                   "email_subject": _extract("EMAIL_SUBJECT", all_labels),
                                   "email_body": _extract("EMAIL_BODY", all_labels)
                               }, error=None)

        except Exception as e:
            self.logger.error(f"MarketingAgent failed: {e}", exc_info=True)
            return AgentOutput(job_id=input['job_id'], status="failed", payload={}, error=str(e))
