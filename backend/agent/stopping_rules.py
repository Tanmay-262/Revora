from typing import Dict, Any, Tuple

def evaluate_stopping_rules(
    payment_state: Dict[str, Any],
    policy_decision: Dict[str, Any],
    attempt_count: int,
    execution_result: Dict[str, Any] = None
) -> Tuple[bool, str]:
    """
    Evaluates explicit stopping rules for a payment recovery workflow.
    
    Returns:
    - should_stop: bool
    - stop_reason: str (e.g. 'PAYMENT_RECOVERED', 'MAX_RETRIES_REACHED', 'CUSTOMER_OPTED_OUT', etc.)
    """
    # 1. Recovery Success
    if execution_result and execution_result.get("status") == "SUCCESS":
        return True, "PAYMENT_RECOVERED"

    # 2. Customer Opt-Out
    if bool(payment_state.get("customer_opted_out", False)):
        return True, "CUSTOMER_OPTED_OUT"

    # 3. Human Review Rejection
    if execution_result and execution_result.get("approval_status") == "REJECTED":
        return True, "HUMAN_REVIEW_REJECTED"

    # 4. Policy Blocked
    if policy_decision and policy_decision.get("decision") == "BLOCK":
        return True, f"POLICY_BLOCKED ({policy_decision.get('rationale', 'Safety rule failure')})"

    # 5. Max Retries Reached
    max_allowed = int(payment_state.get("max_retries", 2))
    if attempt_count >= max_allowed:
        return True, "MAX_RETRIES_REACHED"

    # 6. Invalid Payment State (already paid / refunded)
    status = str(payment_state.get("status", "")).lower()
    if status in ["captured", "paid", "refunded"]:
        return True, f"INVALID_PAYMENT_STATE ({status})"

    # 7. External API Failure repeated abort
    if execution_result and execution_result.get("status") == "API_FAILURE":
        return True, "EXTERNAL_API_FAILURE"

    # No stopping rule triggered -> workflow can continue or await action
    return False, "WORKFLOW_IN_PROGRESS"
