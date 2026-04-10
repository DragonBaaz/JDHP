# PublishingAgent Implementation Guide

## File
`agents/publishing.py`

## Gumroad API Integration

### Create Product (POST)
```python
import requests

def create_gumroad_product(self, title, description, pdf_path, price_usd, tags):
    # Read PDF as binary
    with open(pdf_path, 'rb') as f:
        pdf_bytes = f.read()
    
    response = requests.post(
        "https://api.gumroad.com/v2/products",
        headers={"Authorization": f"Bearer {self.config.GUMROAD_ACCESS_TOKEN}"},
        data={
            "name": title,
            "description": description,
            "price": int(price_usd * 100),  # Gumroad uses cents
            "published": "false",  # ALWAYS false until Gate 3 approval
            "tags": ",".join(tags),
        },
        files={"file": (f"{title}.pdf", pdf_bytes, "application/pdf")}
    )
    response.raise_for_status()
    return response.json()["product"]
```

### INR to USD Conversion
```python
def inr_to_usd(self, inr_amount):
    resp = requests.get(
        f"https://v6.exchangerate-api.com/v6/{self.config.EXCHANGERATE_API_KEY}/pair/INR/USD"
    )
    rate = resp.json()["conversion_rate"]
    return round(inr_amount * rate, 2)
```

### After Gate 3 Approval — Publish
```python
def publish_product(self, product_id):
    requests.put(
        f"https://api.gumroad.com/v2/products/{product_id}",
        headers={"Authorization": f"Bearer {self.config.GUMROAD_ACCESS_TOKEN}"},
        data={"published": "true"}
    )
```

## Important
The `run()` method only creates the product (unpublished). Publishing is a separate method called by the runner after Gate 3 approval — it is NOT part of the agent's `run()` method.
