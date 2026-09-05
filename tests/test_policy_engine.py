import pytest
from backend.policy.engine import PolicyEngine

def test_policy_opt_out_hard_stop():
    engine = PolicyEngine()
    payment = {"amount": 1000.0, "attempt_number": 1, "previous_failures": 0, "customer_opted_out": 1}
    interv = {"intervention": "RETRY_LATER", "probability_success": 0.90}
    rc = {"cause": "TEMPORARY_BANK_FAILURE", "confidence": 0.90}
    
    res = engine.evaluate_policy(payment, interv, rc)
    assert res["decision"] == "BLOCK"
    assert "HARD_STOP" in res["rationale"]

def test_policy_max_retries():
    engine = PolicyEngine(max_retries=2)
    payment = {"amount": 1000.0, "attempt_number": 2, "previous_failures": 1, "customer_opted_out": 0} # total 3 attempts > 2
    interv = {"intervention": "RETRY_LATER", "probability_success": 0.90}
    rc = {"cause": "TEMPORARY_BANK_FAILURE", "confidence": 0.90}
    
    res = engine.evaluate_policy(payment, interv, rc)
    assert res["decision"] == "BLOCK"
    assert "Maximum retry limit" in res["rationale"]

def test_policy_high_value_human_approval():
    engine = PolicyEngine(max_automated_amount=10000.0)
    payment = {"amount": 25000.0, "attempt_number": 1, "previous_failures": 0, "customer_opted_out": 0}
    interv = {"intervention": "RETRY_LATER", "probability_success": 0.90}
    rc = {"cause": "TEMPORARY_BANK_FAILURE", "confidence": 0.90}
    
    res = engine.evaluate_policy(payment, interv, rc)
    assert res["decision"] == "HUMAN_APPROVAL_REQUIRED"
    assert "exceeds automated threshold" in res["rationale"]

def test_policy_allow():
    engine = PolicyEngine(max_automated_amount=10000.0, max_retries=2, min_action_confidence=0.70)
    payment = {"amount": 4999.0, "attempt_number": 1, "previous_failures": 0, "customer_opted_out": 0}
    interv = {"intervention": "RETRY_LATER", "probability_success": 0.85}
    rc = {"cause": "TEMPORARY_BANK_FAILURE", "confidence": 0.90}
    
    res = engine.evaluate_policy(payment, interv, rc)
    assert res["decision"] == "ALLOW"
