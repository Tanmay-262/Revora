import os
import requests
from backend.razorpay.mock_adapter import RazorpayMockAdapter

class RazorpayAdapter:
    """
    Razorpay Test Mode API client adapter with resilient mock sandbox fallback.
    Prevents external API downtime from breaking recovery operations.
    """
    def __init__(self, key_id: str = None, key_secret: str = None):
        self.key_id = key_id or os.getenv("RAZORPAY_KEY_ID")
        self.key_secret = key_secret or os.getenv("RAZORPAY_KEY_SECRET")
        self.base_url = "https://api.razorpay.com/v1"
        self.mock_adapter = RazorpayMockAdapter()
        
        # Determine if test credentials are non-placeholder
        self.is_live_test_api = bool(
            self.key_id and self.key_secret and
            not self.key_id.startswith("rzp_test_your") and
            not self.key_id.startswith("rzp_test_mock")
        )

    def fetch_payment(self, payment_id: str) -> dict:
        if not self.is_live_test_api:
            return self.mock_adapter.fetch_payment(payment_id)
        try:
            resp = requests.get(
                f"{self.base_url}/payments/{payment_id}",
                auth=(self.key_id, self.key_secret),
                timeout=5
            )
            if resp.status_code == 200:
                return resp.json()
            return self.mock_adapter.fetch_payment(payment_id)
        except Exception:
            return self.mock_adapter.fetch_payment(payment_id)

    def create_order(self, amount: float, currency: str = "INR", receipt: str = None) -> dict:
        if not self.is_live_test_api:
            return self.mock_adapter.create_order(amount, currency, receipt)
        try:
            payload = {
                "amount": int(amount * 100),
                "currency": currency,
                "receipt": receipt or "rcpt_rec_01"
            }
            resp = requests.post(
                f"{self.base_url}/orders",
                auth=(self.key_id, self.key_secret),
                json=payload,
                timeout=5
            )
            if resp.status_code in [200, 201]:
                return resp.json()
            return self.mock_adapter.create_order(amount, currency, receipt)
        except Exception:
            return self.mock_adapter.create_order(amount, currency, receipt)

    def create_payment_link(
        self,
        amount: float,
        currency: str = "INR",
        description: str = "Razorpay AI Revenue Recovery Link",
        customer_name: str = "Valued Customer",
        customer_email: str = "customer@example.com",
        customer_contact: str = "+919999999999"
    ) -> dict:
        if not self.is_live_test_api:
            return self.mock_adapter.create_payment_link(amount, currency, description, customer_name, customer_email, customer_contact)
        try:
            payload = {
                "amount": int(amount * 100),
                "currency": currency,
                "accept_partial": False,
                "description": description,
                "customer": {
                    "name": customer_name,
                    "email": customer_email,
                    "contact": customer_contact
                },
                "notify": {"sms": True, "email": True},
                "reminder_enable": True
            }
            resp = requests.post(
                f"{self.base_url}/payment_links",
                auth=(self.key_id, self.key_secret),
                json=payload,
                timeout=5
            )
            if resp.status_code in [200, 201]:
                return resp.json()
            return self.mock_adapter.create_payment_link(amount, currency, description, customer_name, customer_email, customer_contact)
        except Exception:
            return self.mock_adapter.create_payment_link(amount, currency, description, customer_name, customer_email, customer_contact)

    def fetch_payment_link(self, link_id: str) -> dict:
        if not self.is_live_test_api:
            return self.mock_adapter.fetch_payment_link(link_id)
        try:
            resp = requests.get(
                f"{self.base_url}/payment_links/{link_id}",
                auth=(self.key_id, self.key_secret),
                timeout=5
            )
            if resp.status_code == 200:
                return resp.json()
            return self.mock_adapter.fetch_payment_link(link_id)
        except Exception:
            return self.mock_adapter.fetch_payment_link(link_id)

    def cancel_payment_link(self, link_id: str) -> dict:
        if not self.is_live_test_api:
            return self.mock_adapter.cancel_payment_link(link_id)
        try:
            resp = requests.post(
                f"{self.base_url}/payment_links/{link_id}/cancel",
                auth=(self.key_id, self.key_secret),
                timeout=5
            )
            if resp.status_code == 200:
                return resp.json()
            return self.mock_adapter.cancel_payment_link(link_id)
        except Exception:
            return self.mock_adapter.cancel_payment_link(link_id)
