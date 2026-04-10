import os
import re
from datetime import datetime
import mistune
from jinja2 import Environment, FileSystemLoader
from agents.base import BaseAgent, AgentInput, AgentOutput

class DesignAgent(BaseAgent):
    def run(self, input: AgentInput) -> AgentOutput:
        """Convert edited markdown to a professional PDF via Jinja2 + WeasyPrint."""
        self.logger.info(f"Starting DesignAgent for job {input['job_id']}")

        try:
            from weasyprint import HTML, CSS

            edited_markdown = input['payload'].get('edited_markdown', '')
            report_title = input['payload'].get('report_title', 'JDHP Report')
            target_audience = input['payload'].get('target_audience', 'General')
            price_inr = input['payload'].get('price_inr', 1000)

            # Convert markdown to HTML
            html_body = mistune.html(edited_markdown)

            # Render full page via Jinja2 template
            template_dir = os.path.join(os.path.dirname(__file__), '..', 'templates')
            env = Environment(loader=FileSystemLoader(os.path.abspath(template_dir)))
            template = env.get_template('report.html')
            full_html = template.render(
                title=report_title,
                body=html_body,
                audience=target_audience,
                price_inr=price_inr,
                date=datetime.now().strftime("%B %Y")
            )

            # Ensure output directory exists
            output_dir = self.config.OUTPUT_DIR
            os.makedirs(output_dir, exist_ok=True)

            safe_title = re.sub(r'[^a-zA-Z0-9_]', '_', report_title)[:60]
            date_str = datetime.now().strftime("%Y%m%d")
            pdf_filename = f"JDHP_{safe_title}_{date_str}.pdf"
            pdf_path = os.path.join(output_dir, pdf_filename)

            HTML(string=full_html).write_pdf(pdf_path)

            file_size = os.path.getsize(pdf_path)

            # Estimate page count from word count (avg 300 words/page)
            word_count = len(edited_markdown.split())
            page_count = max(1, word_count // 300)

            self.logger.info(f"PDF generated: {pdf_path} ({file_size} bytes, ~{page_count} pages)")

            return AgentOutput(job_id=input['job_id'], status="success",
                               payload={"pdf_path": os.path.abspath(pdf_path),
                                        "page_count": page_count,
                                        "file_size_bytes": file_size},
                               error=None)

        except Exception as e:
            self.logger.error(f"DesignAgent failed: {e}", exc_info=True)
            return AgentOutput(job_id=input['job_id'], status="failed", payload={}, error=str(e))
