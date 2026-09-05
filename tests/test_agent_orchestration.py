import pytest
from backend.agent.orchestrator import AgentOrchestrator

def test_agent_analysis():
    agent = AgentOrchestrator()
    payment = {
        "payment_id": "pay_999999",
        "customer_id": "cust_1234",
        "amount": 4999.0,
        "payment_method": "card",
        "bank": "HDFC",
        "attempt_number": 1,
        "previous_failures": 0,
        "failure_code": "BANK_SERVER_DOWN",
        "bank_failure_rate": 0.60,
        "customer_opted_out": 0,
        "checkout_duration": 40
    }
    
    analysis = agent.analyze_payment(payment)
    assert analysis["payment_id"] == "pay_999999"
    assert analysis["root_cause"]["cause"] == "TEMPORARY_BANK_FAILURE"
    assert len(analysis["ranked_interventions"]) > 0
    assert analysis["policy_result"]["decision"] in ["ALLOW", "HUMAN_APPROVAL_REQUIRED", "BLOCK"]
    assert "audit_events" in analysis

def test_agent_execution_allow():
    agent = AgentOrchestrator()
    payment = {
        "payment_id": "pay_999999",
        "customer_id": "cust_1234",
        "amount": 2000.0,
        "payment_method": "card",
        "bank": "HDFC",
        "attempt_number": 1,
        "previous_failures": 0,
        "failure_code": "BANK_SERVER_DOWN",
        "bank_failure_rate": 0.60,
        "customer_success_rate": 0.90,
        "payment_success_rate": 0.90,
        "customer_opted_out": 0
    }
    analysis = agent.analyze_payment(payment)
    res = agent.execute_recovery_action(payment, analysis)
    assert res["status"] in ["SUCCESS", "ATTEMPT_FAILED", "PENDING_HUMAN_APPROVAL"]
