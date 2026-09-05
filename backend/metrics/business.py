from typing import Dict, Any, List

def calculate_business_metrics(
    all_payments: List[Dict[str, Any]],
    recovery_results: List[Dict[str, Any]],
    baseline_recovered_revenue: float
) -> Dict[str, Any]:
    """
    Computes honest financial and operational metrics for the AI Revenue Recovery system.
    """
    total_txns = len(all_payments)
    failed_txns = total_txns  # all input records represent payment failures
    
    total_revenue_at_risk = float(sum(p.get("amount", 0.0) for p in all_payments))
    
    agent_recovered_revenue = float(sum(
        r.get("recovered_amount", 0.0) for r in recovery_results if r.get("recovered", False)
    ))
    
    recovery_rate = agent_recovered_revenue / total_revenue_at_risk if total_revenue_at_risk > 0 else 0.0
    
    # Calculate recovery uplift over baseline
    if baseline_recovered_revenue > 0:
        recovery_uplift = (agent_recovered_revenue - baseline_recovered_revenue) / baseline_recovered_revenue
    else:
        recovery_uplift = 1.0 if agent_recovered_revenue > 0 else 0.0
        
    total_interventions = len(recovery_results)
    successful_interventions = sum(1 for r in recovery_results if r.get("recovered", False))
    blocked_interventions = sum(1 for r in recovery_results if r.get("status") == "BLOCKED")
    human_escalations = sum(1 for r in recovery_results if r.get("status") == "PENDING_HUMAN_APPROVAL")
    
    total_attempts = sum(p.get("attempt_number", 1) for p in all_payments)
    avg_attempts = total_attempts / total_txns if total_txns > 0 else 1.0
    
    # Breakdown by intervention type
    intervention_breakdown = {}
    for r in recovery_results:
        interv = r.get("selected_intervention", "UNKNOWN")
        if interv not in intervention_breakdown:
            intervention_breakdown[interv] = {"count": 0, "recovered_amount": 0.0, "success_count": 0}
        intervention_breakdown[interv]["count"] += 1
        if r.get("recovered", False):
            intervention_breakdown[interv]["success_count"] += 1
            intervention_breakdown[interv]["recovered_amount"] += r.get("recovered_amount", 0.0)

    return {
        "total_transactions": total_txns,
        "failed_transactions": failed_txns,
        "total_revenue_at_risk": round(total_revenue_at_risk, 2),
        "total_recovered_revenue": round(agent_recovered_revenue, 2),
        "agent_recovered_revenue": round(agent_recovered_revenue, 2),
        "baseline_recovered_revenue": round(baseline_recovered_revenue, 2),
        "recovery_rate": round(recovery_rate, 4),
        "recovery_uplift": round(recovery_uplift, 4),
        "total_interventions": total_interventions,
        "successful_interventions": successful_interventions,
        "blocked_interventions": blocked_interventions,
        "human_escalations": human_escalations,
        "average_attempts_per_payment": round(avg_attempts, 2),
        "intervention_breakdown": intervention_breakdown
    }
