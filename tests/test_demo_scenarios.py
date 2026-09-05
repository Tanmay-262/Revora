import pytest
from backend.agent.orchestrator import AgentOrchestrator
from backend.policy.engine import PolicyEngine
from backend.razorpay.adapter import RazorpayAdapter

def test_scenario_1_automated_recovery():
    """Scenario 1: Standard automated recovery for bank failure."""
    agent = AgentOrchestrator()
    payment = {
        "payment_id": "pay_demo_01",
        "customer_id": "cust_demo_01",
        "amount": 2500.0,
        "payment_method": "netbanking",
        "bank": "SBI",
        "attempt_number": 1,
        "previous_failures": 0,
        "failure_code": "BANK_SERVER_DOWN",
        "bank_failure_rate": 0.65,
        "customer_success_rate": 0.90,
        "payment_success_rate": 0.85,
        "checkout_duration": 30,
        "cart_value": 2500.0,
        "customer_opted_out": 0
    }
    analysis = agent.analyze_payment(payment)
    assert analysis["root_cause"]["cause"] == "TEMPORARY_BANK_FAILURE"
    assert analysis["policy_result"]["decision"] == "ALLOW"

def test_scenario_2_payment_link_recovery():
    """Scenario 2: Customer abandonment triggers payment link intervention."""
    agent = AgentOrchestrator()
    payment = {
        "payment_id": "pay_demo_02",
        "customer_id": "cust_demo_02",
        "amount": 4999.0,
        "payment_method": "upi",
        "bank": "HDFC",
        "attempt_number": 1,
        "previous_failures": 0,
        "failure_code": "USER_DROPPED_OFF",
        "checkout_duration": 150,
        "customer_success_rate": 0.85,
        "customer_opted_out": 0
    }
    analysis = agent.analyze_payment(payment)
    assert analysis["root_cause"]["cause"] == "CUSTOMER_ABANDONMENT"
    assert analysis["selected_intervention"]["intervention"] == "SEND_PAYMENT_LINK"

def test_scenario_3_human_approval_gating():
    """Scenario 3: High-value transaction (> INR 10,000) requires human approval."""
    agent = AgentOrchestrator()
    payment = {
        "payment_id": "pay_demo_03",
        "customer_id": "cust_demo_03",
        "amount": 28000.0, # Exceeds 10,000 threshold
        "payment_method": "card",
        "bank": "ICICI",
        "attempt_number": 1,
        "previous_failures": 0,
        "failure_code": "BANK_SERVER_DOWN",
        "bank_failure_rate": 0.50,
        "customer_opted_out": 0
    }
    analysis = agent.analyze_payment(payment)
    assert analysis["policy_result"]["decision"] == "HUMAN_APPROVAL_REQUIRED"
    
    # Verify execution without approval is gated
    exec_unapproved = agent.execute_recovery_action(payment, analysis, human_approved=False)
    assert exec_unapproved["status"] == "PENDING_HUMAN_APPROVAL"
    
    # Verify execution with approval dispatches action
    exec_approved = agent.execute_recovery_action(payment, analysis, human_approved=True)
    assert exec_approved["status"] in ["SUCCESS", "ATTEMPT_FAILED"]

def test_scenario_4_stopping_rule_max_retries():
    """Scenario 4: Two failed retries triggers MAX_RETRIES_REACHED stopping rule."""
    agent = AgentOrchestrator()
    payment = {
        "payment_id": "pay_demo_04",
        "customer_id": "cust_demo_04",
        "amount": 1500.0,
        "payment_method": "card",
        "bank": "AXIS",
        "attempt_number": 2,
        "previous_failures": 1, # total attempts 3 > max 2
        "failure_code": "CARD_EXPIRED",
        "customer_opted_out": 0
    }
    analysis = agent.analyze_payment(payment)
    assert analysis["policy_result"]["decision"] == "BLOCK"
    assert analysis["stopping_rule"]["should_stop"] == True
    assert "Maximum retry limit" in analysis["policy_result"]["rationale"]

def test_scenario_5_external_api_fallback():
    """Scenario 5: External API down triggers safe mock sandbox fallback."""
    adapter = RazorpayAdapter(key_id="invalid_key", key_secret="invalid_secret")
    link = adapter.create_payment_link(amount=1999.0, description="Test fallback link")
    assert link is not None
    assert "plink_" in link["id"]
