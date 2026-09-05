from backend.razorpay.adapter import RazorpayAdapter

_instance = None

def get_razorpay_client() -> RazorpayAdapter:
    """Returns singleton instance of RazorpayAdapter."""
    global _instance
    if _instance is None:
        _instance = RazorpayAdapter()
    return _instance
