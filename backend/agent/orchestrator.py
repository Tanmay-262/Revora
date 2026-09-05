import os
import joblib
import pandas as pd
import numpy as np
from typing import Dict, Any

from ml.root_cause import classify_root_cause
from ml.interventions import rank_interventions
from backend.policy.engine import PolicyEngine
from backend.agent.stopping_rules import evaluate_stopping_rules
from backend.razorpay.client import get_razorpay_client
from backend.llm.explainability import LLMExplainer

class AgentOrchestrator:
    """
    Stateful recovery agent orchestrating payment diagnosis, intervention selection,
    policy evaluation, Razorpay action dispatch, audit logging, and stopping rules.
    """
    def __init__(self, model_path: str = "ml/artifacts/model.joblib"):
        self.model_path = model_path
        self.pipeline = None
        if os.path.exists(model_path):
            self.pipeline = joblib.load(model_path)
            
        self.policy_engine = PolicyEngine()
        self.razorpay_client = get_razorpay_client()
        self.llm_explainer = LLMExplainer()

    def predict_recovery_probability(self, payment_data: Dict[str, Any]) -> float:
        """Predicts P(recovery) using the trained ML model pipeline."""
        if not self.pipeline:
            return 0.50
            
        defaults = {
            "amount": 1000.0, "cart_value": 1000.0, "payment_method": "card", "bank": "HDFC",
            "attempt_number": 1, "previous_failures": 0, "customer_age_days": 180,
            "customer_success_rate": 0.85, "payment_success_rate": 0.85, "device_type": "mobile_android",
            "failure_code": "BANK_SERVER_DOWN", "failure_class": "TEMPORARY_BANK_FAILURE",
            "checkout_duration": 30, "is_subscription": 0, "customer_opted_out": 0,
            "historical_recovery_rate": 0.75, "bank_failure_rate": 0.05, "hour_of_day": 14, "day_of_week": 2
        }
        full_data = {**defaults, **payment_data}
        df_row = pd.DataFrame([full_data])
        try:
            prob = self.pipeline.predict_proba(df_row)[0, 1]
            return float(np.clip(prob, 0.01, 0.99))
        except Exception:
            return 0.50

    def analyze_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes diagnosis & intervention ranking phase without taking financial action.
        """
        audit_events = []
        
        # Step 1: Detect payment failure
        payment_id = payment_data.get("payment_id", "pay_unknown")
        audit_events.append({
            "event_type": "PAYMENT_FAILURE_DETECTED",
            "actor": "AGENT_ORCHESTRATOR",
            "decision": "FAILURE_DETECTED",
            "reason": f"Payment failure detected for ID {payment_id} (Code: {payment_data.get('failure_code')})"
        })

        # Step 2: Opt-out check
        if bool(payment_data.get("customer_opted_out", False)):
            audit_events.append({
                "event_type": "CUSTOMER_OPT_OUT_DETECTED",
                "actor": "POLICY_ENGINE",
                "decision": "HARD_STOP",
                "reason": "Customer opted out of communications"
            })
            return {
                "payment_id": payment_id,
                "p_recovery": 0.0,
                "root_cause": {"cause": "CUSTOMER_OPTED_OUT", "confidence": 1.0, "evidence": ["customer_opt_out_flag"]},
                "ranked_interventions": [],
                "selected_intervention": {"intervention": "NO_ACTION", "expected_recovery_value": 0.0, "probability_success": 0.0},
                "policy_result": {"decision": "BLOCK", "rationale": "HARD_STOP: Customer opted out"},
                "stopping_rule": {"should_stop": True, "stop_reason": "CUSTOMER_OPTED_OUT"},
                "llm_explanation": "Customer opted out of recovery communications.",
                "audit_events": audit_events
            }

        # Step 3: ML Recovery Probability Prediction
        p_recovery = self.predict_recovery_probability(payment_data)
        audit_events.append({
            "event_type": "RISK_SCORE_CALCULATED",
            "actor": "ML_MODEL",
            "decision": f"P_RECOVERY={p_recovery:.4f}",
            "reason": f"ML model calculated recovery probability of {p_recovery*100:.1f}%"
        })

        # Step 4: Root Cause Classification
        root_cause_info = classify_root_cause(payment_data)
        audit_events.append({
            "event_type": "ROOT_CAUSE_IDENTIFIED",
            "actor": "ROOT_CAUSE_CLASSIFIER",
            "decision": root_cause_info["cause"],
            "reason": f"Evidence: {', '.join(root_cause_info['evidence'])} (Confidence: {root_cause_info['confidence']*100:.1f}%)"
        })

        # Step 5: Rank Candidate Interventions by Expected Value
        ranked_interventions = rank_interventions(payment_data, p_recovery, root_cause_info)
        selected_intervention = ranked_interventions[0] if ranked_interventions else {
            "intervention": "HUMAN_REVIEW", "probability_success": 0.1, "expected_recovery_value": 0.0
        }
        
        audit_events.append({
            "event_type": "INTERVENTIONS_RANKED",
            "actor": "EXPECTED_VALUE_ENGINE",
            "decision": selected_intervention["intervention"],
            "reason": f"Ranked {len(ranked_interventions)} options. Selected '{selected_intervention['intervention']}' with Expected Value INR {selected_intervention['expected_recovery_value']:,.2f}"
        })

        # Step 6: Policy Engine Evaluation
        policy_result = self.policy_engine.evaluate_policy(payment_data, selected_intervention, root_cause_info)
        audit_events.append({
            "event_type": "POLICY_CHECK",
            "actor": "POLICY_ENGINE",
            "decision": policy_result["decision"],
            "reason": policy_result["rationale"]
        })

        # Step 7: Check Stopping Rules
        should_stop, stop_reason = evaluate_stopping_rules(
            payment_state=payment_data,
            policy_decision=policy_result,
            attempt_count=int(payment_data.get("attempt_number", 1))
        )
        
        # Step 8: LLM Summary Explanation
        llm_explanation = self.llm_explainer.explain_root_cause_and_risk(
            payment_data, root_cause_info, selected_intervention, policy_result
        )

        return {
            "payment_id": payment_id,
            "p_recovery": round(p_recovery, 4),
            "root_cause": root_cause_info,
            "ranked_interventions": ranked_interventions,
            "selected_intervention": selected_intervention,
            "policy_result": policy_result,
            "stopping_rule": {"should_stop": should_stop, "stop_reason": stop_reason},
            "llm_explanation": llm_explanation,
            "audit_events": audit_events
        }

    def execute_recovery_action(
        self,
        payment_data: Dict[str, Any],
        analysis_result: Dict[str, Any],
        human_approved: bool = False
    ) -> Dict[str, Any]:
        """
        Executes bounded recovery intervention if policy ALLOWS or HUMAN_APPROVED.
        """
        policy_decision = analysis_result["policy_result"]["decision"]
        selected = analysis_result["selected_intervention"]
        intervention_name = selected["intervention"]
        payment_id = payment_data["payment_id"]
        amount = float(payment_data["amount"])

        audit_events = []

        # Check authorization
        if policy_decision == "BLOCK":
            audit_events.append({
                "event_type": "ACTION_BLOCKED",
                "actor": "POLICY_ENGINE",
                "decision": "BLOCKED",
                "reason": analysis_result["policy_result"]["rationale"]
            })
            return {
                "status": "BLOCKED",
                "message": "Action denied by safety policy engine.",
                "recovered": False,
                "audit_events": audit_events
            }

        if policy_decision == "HUMAN_APPROVAL_REQUIRED" and not human_approved:
            audit_events.append({
                "event_type": "HUMAN_APPROVAL_ESCALATED",
                "actor": "POLICY_ENGINE",
                "decision": "PENDING_APPROVAL",
                "reason": "Action requires human operator approval before execution."
            })
            return {
                "status": "PENDING_HUMAN_APPROVAL",
                "message": "Escalated to human operator approval queue.",
                "recovered": False,
                "audit_events": audit_events
            }

        # Dispatch intervention via Razorpay Adapter / Recovery Handlers
        audit_events.append({
            "event_type": "ACTION_DISPATCHED",
            "actor": "RECOVERY_EXECUTOR",
            "decision": intervention_name,
            "reason": f"Executing {intervention_name} for payment {payment_id}"
        })

        execution_result = {}

        if intervention_name == "SEND_PAYMENT_LINK":
            link_res = self.razorpay_client.create_payment_link(
                amount=amount,
                description=f"Recovery link for {payment_id}",
                customer_name=payment_data.get("customer_id", "Customer")
            )
            execution_result = {
                "action": "SEND_PAYMENT_LINK",
                "payment_link_id": link_res.get("id"),
                "short_url": link_res.get("short_url"),
                "status": link_res.get("status")
            }

        elif intervention_name == "RETRY_LATER":
            # Schedule retry window
            execution_result = {
                "action": "RETRY_LATER",
                "retry_delay_minutes": 30,
                "status": "SCHEDULED"
            }

        elif intervention_name == "ALTERNATIVE_PAYMENT_METHOD":
            execution_result = {
                "action": "ALTERNATIVE_PAYMENT_METHOD",
                "suggested_methods": ["UPI", "CARD"],
                "status": "PROMPTED"
            }

        else: # HUMAN_REVIEW
            execution_result = {
                "action": "HUMAN_REVIEW",
                "status": "ASSIGNED_TO_OPERATOR"
            }

        # Determine recovery success based on conditional probability (deterministic simulation)
        # Using payment_id seed for reproducible evaluation
        digits = ''.join(filter(str.isdigit, payment_id))
        row_seed = int(digits) % 100000 if digits else abs(hash(payment_id)) % 100000
        rng = np.random.RandomState(row_seed)
        
        recovered_success = rng.rand() < selected["probability_success"]
        
        if recovered_success:
            audit_events.append({
                "event_type": "PAYMENT_RECOVERED",
                "actor": "RECOVERY_VERIFIER",
                "decision": "SUCCESS",
                "reason": f"Payment successfully recovered! INR {amount:,.2f} captured."
            })
            return {
                "status": "SUCCESS",
                "recovered": True,
                "recovered_amount": amount,
                "execution_details": execution_result,
                "audit_events": audit_events
            }
        else:
            audit_events.append({
                "event_type": "RECOVERY_ATTEMPT_FAILED",
                "actor": "RECOVERY_VERIFIER",
                "decision": "FAILED",
                "reason": f"Recovery action executed but transaction was not recovered."
            })
            return {
                "status": "ATTEMPT_FAILED",
                "recovered": False,
                "recovered_amount": 0.0,
                "execution_details": execution_result,
                "audit_events": audit_events
            }
