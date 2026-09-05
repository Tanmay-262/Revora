import uuid
from datetime import datetime

class RazorpayMockAdapter:
    """
    Mock sandbox adapter simulating Razorpay API endpoints for offline or test mode execution.
    100% resilient and deterministic fallback.
    """
    def __init__(self):
        self.mode = "SIMULATION_SANDBOX"

    def fetch_payment(self, payment_id: str) -> dict:
        return {
            "id": payment_id,
            "entity": "payment",
            "amount": 499900,
            "currency": "INR",
            "status": "failed",
            "method": "card",
            "error_code": "BAD_REQUEST_GATEWAY_TIMEOUT",
            "error_description": "Bank gateway timed out during processing",
            "created_at": int(datetime.utcnow().timestamp())
        }

    def create_order(self, amount: float, currency: str = "INR", receipt: str = None) -> dict:
        order_id = f"order_{uuid.uuid4().hex[:14]}"
        return {
            "id": order_id,
            "entity": "order",
            "amount": int(amount * 100),
            "currency": currency,
            "receipt": receipt or f"rcpt_{uuid.uuid4().hex[:8]}",
            "status": "created",
            "created_at": int(datetime.utcnow().timestamp())
        }

    def create_payment_link(
        self,
        amount: float,
        currency: str = "INR",
        description: str = "Razorpay AI Recovery Link",
        customer_name: str = "Valued Customer",
        customer_email: str = "customer@example.com",
        customer_contact: str = "+919999999999"
    ) -> dict:
        link_id = f"plink_{uuid.uuid4().hex[:14]}"
        short_url = f"https://rzp.io/i/rec_{link_id[-8:]}"
        return {
            "id": link_id,
            "entity": "payment_link",
            "amount": int(amount * 100),
            "currency": currency,
            "short_url": short_url,
            "status": "created",
            "description": description,
            "customer": {
                "name": customer_name,
                "email": customer_email,
                "contact": customer_contact
            },
            "created_at": int(datetime.utcnow().timestamp())
        }

    def fetch_payment_link(self, link_id: str) -> dict:
        return {
            "id": link_id,
            "entity": "payment_link",
            "status": "paid",
            "amount_paid": 499900,
            "updated_at": int(datetime.utcnow().timestamp())
        }

    def cancel_payment_link(self, link_id: str) -> dict:
        return {
            "id": link_id,
            "entity": "payment_link",
            "status": "cancelled",
            "updated_at": int(datetime.utcnow().timestamp())
        }
