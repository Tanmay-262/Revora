from typing import Dict, List, Any

# Intervention cost & friction parameters (in INR)
INTERVENTION_METRICS = {
    "RETRY_LATER": {
        "cost": 10.0,
        "friction": 20.0,
        "description": "Schedule automated retry after bank recovery window"
    },
    "SEND_PAYMENT_LINK": {
        "cost": 25.0,
        "friction": 50.0,
        "description": "Generate and send interactive Razorpay payment link via SMS/Email"
    },
    "ALTERNATIVE_PAYMENT_METHOD": {
        "cost": 15.0,
        "friction": 100.0,
        "description": "Prompt customer to switch payment instrument (e.g. Card -> UPI)"
    },
    "HUMAN_REVIEW": {
        "cost": 200.0,
        "friction": 150.0,
        "description": "Escalate to high-value manual operations team for manual recovery"
    }
}

def rank_interventions(
    payment_data: Dict[str, Any],
    p_recovery_base: float,
    root_cause_info: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Computes conditional probability P(success | intervention) and Expected Recovery Value
    for all candidate interventions.
    
    Expected Recovery Value = P(success | intervention) * Amount - Intervention Cost - Friction Cost
    
    Returns sorted list of intervention options ranked by Expected Recovery Value descending.
    """
    amount = float(payment_data.get("amount", 0.0))
    cause = root_cause_info.get("cause", "UNKNOWN")
    cause_conf = float(root_cause_info.get("confidence", 0.5))
    customer_opted_out = bool(payment_data.get("customer_opted_out", 0))
    is_subscription = bool(payment_data.get("is_subscription", 0))
    attempt_number = int(payment_data.get("attempt_number", 1))
    
    ranked_results = []
    
    for intervention, config in INTERVENTION_METRICS.items():
        if customer_opted_out:
            p_conditional = 0.0
        else:
            # Conditional probability multiplier based on intervention suitability
            multiplier = 0.5  # default
            
            if intervention == "RETRY_LATER":
                if cause == "TEMPORARY_BANK_FAILURE":
                    multiplier = 1.15
                elif cause == "INSUFFICIENT_FUNDS":
                    multiplier = 0.85
                elif cause == "PAYMENT_METHOD_FAILURE":
                    multiplier = 0.20 # Retrying invalid card fails
                elif cause == "CUSTOMER_ABANDONMENT":
                    multiplier = 0.30
                    
            elif intervention == "SEND_PAYMENT_LINK":
                if cause == "CUSTOMER_ABANDONMENT":
                    multiplier = 1.25
                elif is_subscription:
                    multiplier = 1.20
                elif cause == "PAYMENT_METHOD_FAILURE":
                    multiplier = 0.90
                elif cause == "TEMPORARY_BANK_FAILURE":
                    multiplier = 0.70
                    
            elif intervention == "ALTERNATIVE_PAYMENT_METHOD":
                if cause == "PAYMENT_METHOD_FAILURE":
                    multiplier = 1.30
                elif cause == "INSUFFICIENT_FUNDS":
                    multiplier = 1.05
                elif cause == "TEMPORARY_BANK_FAILURE":
                    multiplier = 0.80
                elif cause == "CUSTOMER_ABANDONMENT":
                    multiplier = 0.60
                    
            elif intervention == "HUMAN_REVIEW":
                if cause == "UNKNOWN":
                    multiplier = 1.10
                elif amount > 25000:
                    multiplier = 1.05
                else:
                    multiplier = 0.70
                    
            # High attempt count reduces conditional success rate
            if attempt_number >= 2:
                multiplier *= 0.85
                
            p_conditional = min(0.95, max(0.01, p_recovery_base * multiplier * cause_conf))
            
        cost = config["cost"]
        friction = config["friction"]
        
        # Expected Recovery Value formula:
        expected_recovery_value = (p_conditional * amount) - cost - friction
        expected_recovery_value = round(float(expected_recovery_value), 2)
        
        ranked_results.append({
            "intervention": intervention,
            "probability_success": round(float(p_conditional), 4),
            "recoverable_amount": amount,
            "intervention_cost": cost,
            "friction_cost": friction,
            "expected_recovery_value": expected_recovery_value,
            "description": config["description"]
        })
        
    # Sort descending by expected_recovery_value
    ranked_results.sort(key=lambda x: x["expected_recovery_value"], reverse=True)
    return ranked_results

if __name__ == "__main__":
    sample_payment = {"amount": 4999.0, "customer_opted_out": 0, "attempt_number": 1, "is_subscription": 0}
    sample_rc = {"cause": "TEMPORARY_BANK_FAILURE", "confidence": 0.91}
    rankings = rank_interventions(sample_payment, 0.65, sample_rc)
    print("Ranked Interventions Sample:")
    for r in rankings:
        print(f"- {r['intervention']}: P={r['probability_success']*100:.1f}%, Expected Recovery: INR {r['expected_recovery_value']:,.2f}")
