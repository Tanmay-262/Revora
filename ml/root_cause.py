import re

def classify_root_cause(payment_data: dict) -> dict:
    """
    Diagnoses the root cause of a failed payment using deterministic evidence rules.
    
    Categories:
    - TEMPORARY_BANK_FAILURE
    - PAYMENT_METHOD_FAILURE
    - CUSTOMER_ABANDONMENT
    - INSUFFICIENT_FUNDS
    - UNKNOWN
    
    Returns dict with cause, confidence score (0.0 to 1.0), and explicit evidence array.
    """
    failure_code = str(payment_data.get("failure_code", "")).upper()
    bank_failure_rate = float(payment_data.get("bank_failure_rate", 0.0))
    checkout_duration = float(payment_data.get("checkout_duration", 0))
    previous_failures = int(payment_data.get("previous_failures", 0))
    payment_method = str(payment_data.get("payment_method", "")).lower()
    
    evidence = []
    
    # 1. Deterministic check: INSUFFICIENT_FUNDS
    if "INSUFFICIENT_FUNDS" in failure_code or "LIMIT_EXCEEDED" in failure_code:
        evidence.append(f"failure_code_indicates_insufficient_funds ({failure_code})")
        return {
            "cause": "INSUFFICIENT_FUNDS",
            "confidence": 0.95,
            "evidence": evidence
        }
        
    # 2. Deterministic check: TEMPORARY_BANK_FAILURE
    if bank_failure_rate > 0.35:
        evidence.append(f"bank_failure_rate_elevated ({bank_failure_rate*100:.1f}% > 35.0%)")
    if any(k in failure_code for k in ["BANK_SERVER_DOWN", "GATEWAY_TIMEOUT", "NETWORK_ERROR", "TIMEOUT"]):
        evidence.append(f"failure_code_matches_temporary_bank_error ({failure_code})")
        
    if len(evidence) >= 2:
        return {
            "cause": "TEMPORARY_BANK_FAILURE",
            "confidence": 0.92,
            "evidence": evidence
        }
    elif len(evidence) == 1 and bank_failure_rate > 0.25:
        return {
            "cause": "TEMPORARY_BANK_FAILURE",
            "confidence": 0.82,
            "evidence": evidence
        }
        
    # 3. Deterministic check: PAYMENT_METHOD_FAILURE
    evidence_pm = []
    if any(k in failure_code for k in ["CARD_EXPIRED", "UPI_PIN_INVALID", "METHOD_NOT_SUPPORTED", "DECLINED"]):
        evidence_pm.append(f"failure_code_matches_payment_method_issue ({failure_code})")
    if previous_failures >= 2 and bank_failure_rate < 0.15:
        evidence_pm.append(f"repeated_failures_on_single_payment_method ({previous_failures} attempts)")
        
    if evidence_pm:
        return {
            "cause": "PAYMENT_METHOD_FAILURE",
            "confidence": 0.88,
            "evidence": evidence_pm
        }
        
    # 4. Deterministic check: CUSTOMER_ABANDONMENT
    evidence_ab = []
    if any(k in failure_code for k in ["CHECKOUT_TIMEOUT", "OTP_NOT_ENTERED", "USER_DROPPED_OFF"]):
        evidence_ab.append(f"failure_code_indicates_customer_dropoff ({failure_code})")
    if checkout_duration > 120:
        evidence_ab.append(f"long_checkout_session_before_failure ({checkout_duration}s)")
        
    if evidence_ab:
        return {
            "cause": "CUSTOMER_ABANDONMENT",
            "confidence": 0.85,
            "evidence": evidence_ab
        }
        
    # 5. Fallback check based on high bank failure rate alone
    if bank_failure_rate > 0.20:
        return {
            "cause": "TEMPORARY_BANK_FAILURE",
            "confidence": 0.70,
            "evidence": [f"bank_failure_rate_above_baseline ({bank_failure_rate*100:.1f}%)"]
        }
        
    # 6. Default UNKNOWN
    return {
        "cause": "UNKNOWN",
        "confidence": 0.50,
        "evidence": [f"unrecognized_failure_pattern (code={failure_code}, bank_fail={bank_failure_rate})"]
    }

if __name__ == "__main__":
    test_payment = {
        "failure_code": "BANK_SERVER_DOWN",
        "bank_failure_rate": 0.55,
        "checkout_duration": 30,
        "previous_failures": 1,
        "payment_method": "netbanking"
    }
    print("Test root cause diagnosis:", classify_root_cause(test_payment))
