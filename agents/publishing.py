import os
import requests
from agents.base import BaseAgent, AgentInput, AgentOutput

class PublishingAgent(BaseAgent):
    def _inr_to_usd(self, inr_amount: int) -> float:
        resp = requests.get(
            f"https://v6.exchangerate-api.com/v6/{self.config.EXCHANGERATE_API_KEY}/pair/INR/USD",
            timeout=10
        )
        resp.raise_for_status()
        rate = resp.json()["conversion_rate"]
        return round(inr_amount * rate, 2)

    def run(self, input: AgentInput) -> AgentOutput:
        """Upload PDF to Gumroad as an UNPUBLISHED product. Gate 3 triggers publish."""
        self.logger.info(f"Starting PublishingAgent for job {input['job_id']}")

        try:
            pdf_path = input['payload'].get('pdf_path', '')
            report_title = input['payload'].get('report_title', 'JDHP Report')
            description = input['payload'].get('description_markdown', 'Research Report by JDHP.')
            price_inr = input['payload'].get('price_inr', 1000)
            tags = input['payload'].get('tags', ['research', 'india'])

            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF not found: {pdf_path}")

            price_usd = self._retry_api_call(self._inr_to_usd, price_inr)

            def _create_listing():
                with open(pdf_path, 'rb') as f:
                    pdf_bytes = f.read()
                response = requests.post(
                    "https://api.gumroad.com/v2/products",
                    headers={"Authorization": f"Bearer {self.config.GUMROAD_ACCESS_TOKEN}"},
                    data={
                        "name": report_title,
                        "description": description,
                        "price": int(price_usd * 100),
                        "published": "false",
                        "tags": ",".join(tags),
                    },
                    files={"file": (f"{report_title.replace(' ', '_')}.pdf", pdf_bytes, "application/pdf")},
                    timeout=60
                )
                response.raise_for_status()
                return response.json()["product"]

            product = self._retry_api_call(_create_listing)

            return AgentOutput(job_id=input['job_id'], status="needs_human",
                               payload={"gumroad_product_id": product["id"],
                                        "gumroad_url": product.get("short_url", ""),
                                        "published_at": None},
                               error=None)

        except Exception as e:
            self.logger.error(f"PublishingAgent failed: {e}", exc_info=True)
            return AgentOutput(job_id=input['job_id'], status="failed", payload={}, error=str(e))

    def publish(self, product_id: str):
        """Call this after Gate 3 approval to make the product live."""
        requests.put(
            f"https://api.gumroad.com/v2/products/{product_id}",
            headers={"Authorization": f"Bearer {self.config.GUMROAD_ACCESS_TOKEN}"},
            data={"published": "true"},
            timeout=15
        ).raise_for_status()
        self.logger.info(f"Product {product_id} published on Gumroad.")
