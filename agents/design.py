"""
design.py — Enhanced with weasyprint dependency validation

Changes from original:
- Added early check for weasyprint system dependencies
- Provides helpful error message with installation command
- Validates PDF was actually created before returning success
"""
import os
from agents.base import BaseAgent, AgentInput, AgentOutput

class DesignAgent(BaseAgent):
    def run(self, input: AgentInput) -> AgentOutput:
        """
        Convert markdown to PDF using weasyprint + Jinja2 template.
        
        Requires system libraries:
        - libcairo2
        - libpango-1.0-0
        - libgdk-pixbuf2.0-0
        - libffi-dev
        """
        self.logger.info(f"Starting DesignAgent for job {input['job_id']}")

        try:
            # Early validation: check weasyprint dependencies
            try:
                from weasyprint import HTML, CSS
                from jinja2 import Environment, FileSystemLoader
                import mistune
            except ImportError as e:
                self.logger.error(f"Missing required library: {e}")
                
                # Determine if it's a Python or system dependency issue
                if 'weasyprint' in str(e).lower() or 'cairo' in str(e).lower():
                    error_msg = (
                        "PDF generation failed: system dependencies missing.\n\n"
                        "Install required libraries:\n"
                        "  Ubuntu/Debian: sudo apt-get install -y libcairo2 libpango-1.0-0 libgdk-pixbuf2.0-0 libffi-dev\n"
                        "  macOS: brew install cairo pango gdk-pixbuf libffi\n\n"
                        "Then reinstall weasyprint: pip install --force-reinstall weasyprint"
                    )
                else:
                    error_msg = f"Missing Python dependency: {e}\nRun: pip install -r requirements.txt"
                
                return AgentOutput(
                    job_id=input['job_id'],
                    status="failed",
                    payload={},
                    error=error_msg
                )

            edited_markdown = input['payload'].get('edited_markdown', '')
            report_title = input['payload'].get('report_title', 'Research Report')
            target_audience = input['payload'].get('target_audience', 'general')
            price_inr = input['payload'].get('price_inr', 1000)

            if not edited_markdown:
                self.logger.error("No markdown content provided")
                return AgentOutput(
                    job_id=input['job_id'],
                    status="failed",
                    payload={},
                    error="No edited_markdown in payload"
                )

            # Convert markdown to HTML using mistune
            markdown_parser = mistune.create_markdown()
            html_content = markdown_parser(edited_markdown)

            # Load Jinja2 template
            template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
            env = Environment(loader=FileSystemLoader(template_dir))
            template = env.get_template('report.html')

            from datetime import datetime
            # Render with variable names matching the template (title, audience, body, date)
            rendered_html = template.render(
                title=report_title,
                body=html_content,
                audience=target_audience,
                price_inr=price_inr,
                date=datetime.utcnow().strftime('%B %Y'),
            )

            # Generate PDF
            output_dir = self.config.OUTPUT_DIR
            os.makedirs(output_dir, exist_ok=True)
            
            # Sanitize filename
            safe_title = "".join(c for c in report_title if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_title = safe_title.replace(' ', '_')[:50]  # Limit length
            pdf_filename = f"{safe_title}_{input['job_id'][:8]}.pdf"
            pdf_path = os.path.join(output_dir, pdf_filename)

            self.logger.info(f"Generating PDF: {pdf_path}")
            
            # Generate PDF with weasyprint
            HTML(string=rendered_html).write_pdf(pdf_path)

            # Validate PDF was actually created
            if not os.path.exists(pdf_path):
                self.logger.error("PDF file was not created")
                return AgentOutput(
                    job_id=input['job_id'],
                    status="failed",
                    payload={},
                    error="PDF generation failed: file not created"
                )
            
            # Check PDF has content (at least 1KB)
            file_size = os.path.getsize(pdf_path)
            if file_size < 1024:
                self.logger.warning(f"PDF suspiciously small: {file_size} bytes")
                return AgentOutput(
                    job_id=input['job_id'],
                    status="needs_retry",
                    payload={"pdf_path": pdf_path, "file_size_bytes": file_size},
                    error=f"PDF too small ({file_size} bytes), likely corrupted"
                )

            self.logger.info(f"PDF generated successfully: {file_size} bytes")
            return AgentOutput(
                job_id=input['job_id'],
                status="success",
                payload={
                    "pdf_path": pdf_path,
                    "file_size_bytes": file_size,
                    "filename": pdf_filename
                },
                error=None
            )

        except Exception as e:
            self.logger.error(f"DesignAgent failed: {e}", exc_info=True)
            return AgentOutput(
                job_id=input['job_id'],
                status="failed",
                payload={},
                error=str(e)
            )