import os
from typing import Dict, Any

class PolicyEngine:
    """
    Deterministic safety & guardrail engine for AI Revenue Recovery.
    Enforces strict monetary, retry count, confidence, and opt-out limits.
    """
    def __init__(
        self,
        max_retries: int = None,
        max_automated_amount: float = None,
        min_action_confidence: float = None
    ):
        self.max_retries = max_retries or int(os.getenv("MAX_RETRIES", 2))
        self.max_automated_amount = max_automated_amount or float(os.getenv("MAX_AUTOMATED_AMOUNT", 10000.0))
        self.min_action_confidence = min_action_confidence or float(os.getenv("MIN_ACTION_CONFIDENCE", 0.70))

    def evaluate_policy(
        self,
        payment_data: Dict[str, Any],
        selected_intervention: Dict[str, Any],
        root_cause_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluates safety policies against a candidate payment recovery action.
        Returns:
        - decision: "ALLOW" | "BLOCK" | "HUMAN_APPROVAL_REQUIRED"
        - policy_rules_evaluated: List of rule results
        - rationale: Explanation summary string
        """
        amount = float(payment_data.get("amount", 0.0))
        attempt_number = int(payment_data.get("attempt_number", 1))
        previous_failures = int(payment_data.get("previous_failures", 0))
        customer_opted_out = bool(payment_data.get("customer_opted_out", 0))
        
        intervention_name = selected_intervention.get("intervention", "NONE")
        p_success = float(selected_intervention.get("probability_success", 0.0))
        cause_confidence = float(root_cause_info.get("confidence", 0.0))
        
        rules_evaluated = []
        
        # Rule 1: Customer Opt-Out Check (HARD STOP)
        if customer_opted_out:
            rules_evaluated.append({"rule": "CUSTOMER_OPT_OUT", "status": "FAIL", "reason": "Customer explicitly opted out of communications"})
            return {
                "decision": "BLOCK",
                "rules_evaluated": rules_evaluated,
                "rationale": "HARD_STOP: Customer has opted out of automated communications."
            }
        else:
            rules_evaluated.append({"rule": "CUSTOMER_OPT_OUT", "status": "PASS", "reason": "Customer active"})

        # Rule 2: Max Retries Exceeded Check
        total_attempts = attempt_number + previous_failures
        if total_attempts > self.max_retries:
            rules_evaluated.append({"rule": "MAX_RETRIES_LIMIT", "status": "FAIL", "reason": f"Total attempts ({total_attempts}) exceeds limit of {self.max_retries}"})
            return {
                "decision": "BLOCK",
                "rules_evaluated": rules_evaluated,
                "rationale": f"BLOCK: Maximum retry limit of {self.max_retries} attempts reached."
            }
        else:
            rules_evaluated.append({"rule": "MAX_RETRIES_LIMIT", "status": "PASS", "reason": f"Attempts ({total_attempts}) within limit ({self.max_retries})"})

        # Rule 3: Monetary Threshold Check (Requires Human Approval if > MAX_AUTOMATED_AMOUNT)
        needs_human_for_amount = amount > self.max_automated_amount
        if needs_human_for_amount:
            rules_evaluated.append({"rule": "MONETARY_THRESHOLD", "status": "REQUIRE_HUMAN", "reason": f"Amount INR {amount:,.2f} exceeds auto threshold INR {self.max_automated_amount:,.2f}"})
        else:
            rules_evaluated.append({"rule": "MONETARY_THRESHOLD", "status": "PASS", "reason": f"Amount INR {amount:,.2f} within automated limit"})

        # Rule 4: Minimum Action Confidence Check
        needs_human_for_confidence = p_success < self.min_action_confidence or cause_confidence < self.min_action_confidence
        if needs_human_for_confidence:
            rules_evaluated.append({
                "rule": "MIN_CONFIDENCE_THRESHOLD",
                "status": "REQUIRE_HUMAN",
                "reason": f"Action probability ({p_success*100:.1f}%) or root cause confidence ({cause_confidence*100:.1f}%) below minimum required ({self.min_action_confidence*100:.1f}%)"
            })
        else:
            rules_evaluated.append({"rule": "MIN_CONFIDENCE_THRESHOLD", "status": "PASS", "reason": "Confidence meets or exceeds safety threshold"})

        # Rule 5: Specific Human Review Intervention
        if intervention_name == "HUMAN_REVIEW":
            return {
                "decision": "HUMAN_APPROVAL_REQUIRED",
                "rules_evaluated": rules_evaluated,
                "rationale": "HUMAN_APPROVAL_REQUIRED: Selected intervention explicitly mandates manual operator review."
            }

        # Combine checks
        if needs_human_for_amount or needs_human_for_confidence:
            reasons = []
            if needs_human_for_amount:
                reasons.append(f"Transaction amount (INR {amount:,.2f}) exceeds automated threshold (INR {self.max_automated_amount:,.2f})")
            if needs_human_for_confidence:
                reasons.append(f"Model confidence ({p_success*100:.1f}%) below minimum automation threshold ({self.min_action_confidence*100:.1f}%)")
            
            return {
                "decision": "HUMAN_APPROVAL_REQUIRED",
                "rules_evaluated": rules_evaluated,
                "rationale": "HUMAN_APPROVAL_REQUIRED: " + "; ".join(reasons)
            }

        # All pass -> ALLOW
        return {
            "decision": "ALLOW",
            "rules_evaluated": rules_evaluated,
            "rationale": f"ALLOW: All policy rules passed. Bounded automated recovery via {intervention_name} authorized."
        }

if __name__ == "__main__":
    engine = PolicyEngine()
    test_pay = {"amount": 15000.0, "attempt_number": 1, "previous_failures": 0, "customer_opted_out": 0}
    test_interv = {"intervention": "RETRY_LATER", "probability_success": 0.85}
    test_rc = {"cause": "TEMPORARY_BANK_FAILURE", "confidence": 0.90}
    res = engine.evaluate_policy(test_pay, test_interv, test_rc)
    print("Policy Evaluation Test Result:", res)
