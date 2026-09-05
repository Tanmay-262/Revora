import os
import sys
import json
import pandas as pd
from typing import Dict, Any

sys.path.insert(0, os.path.abspath("."))

from backend.agent.orchestrator import AgentOrchestrator
from backend.metrics.business import calculate_business_metrics
from ml.baseline import run_baseline_simulation

def run_batch_evaluation(
    dataset_path: str = "ml/data/payments_dataset.csv",
    limit: int = 1000,
    output_path: str = "evaluation/batch_results.json"
) -> Dict[str, Any]:
    """
    Executes automated batch evaluation of AI Revenue Recovery Agent over dataset.
    Compares AI agent recovery performance directly against the baseline simulation.
    """
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset file not found at {dataset_path}")
        
    df = pd.read_csv(dataset_path)
    if limit and limit < len(df):
        df = df.head(limit)
        
    payments_list = df.to_dict(orient="records")
    
    # 1. Run baseline simulation for benchmark comparison
    baseline_metrics = run_baseline_simulation(dataset_path, "evaluation/baseline_metrics.json")
    # Scale baseline recovered revenue to current batch sample limit if truncated
    sample_ratio = len(payments_list) / 10000.0 if len(df) <= 10000 else 1.0
    scaled_baseline_recovered = baseline_metrics["total_recovered_revenue"] * sample_ratio

    # 2. Run AI Agent Orchestrator over each payment in batch
    agent = AgentOrchestrator()
    results_list = []

    for pay in payments_list:
        analysis = agent.analyze_payment(pay)
        
        # In batch evaluation, simulate human operator approval for escalated high-value items if model confidence >= 70%
        policy_decision = analysis["policy_result"]["decision"]
        human_approved = False
        if policy_decision == "HUMAN_APPROVAL_REQUIRED" and analysis["p_recovery"] >= 0.70:
            human_approved = True
            
        exec_res = agent.execute_recovery_action(pay, analysis, human_approved=human_approved)
        
        results_list.append({
            "payment_id": pay["payment_id"],
            "amount": pay["amount"],
            "failure_class": pay["failure_class"],
            "p_recovery": analysis["p_recovery"],
            "root_cause": analysis["root_cause"]["cause"],
            "selected_intervention": analysis["selected_intervention"]["intervention"],
            "expected_recovery_value": analysis["selected_intervention"]["expected_recovery_value"],
            "policy_decision": analysis["policy_result"]["decision"],
            "status": exec_res["status"],
            "recovered": exec_res.get("recovered", False),
            "recovered_amount": exec_res.get("recovered_amount", 0.0)
        })
        
    # 3. Calculate business metrics
    metrics = calculate_business_metrics(payments_list, results_list, scaled_baseline_recovered)
    
    output_data = {
        "batch_id": f"batch_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}",
        "record_count": len(payments_list),
        "business_metrics": metrics,
        "sample_records": results_list[:20]
    }
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2)
        
    print("=" * 60)
    print("AI REVENUE RECOVERY AGENT — BATCH EVALUATION RESULTS")
    print("=" * 60)
    print(f"Total Transactions Evaluated: {metrics['total_transactions']:,}")
    print(f"Total Revenue At Risk:        INR {metrics['total_revenue_at_risk']:,.2f}")
    print(f"Baseline Recovered Revenue:   INR {metrics['baseline_recovered_revenue']:,.2f}")
    print(f"AI Agent Recovered Revenue:   INR {metrics['agent_recovered_revenue']:,.2f}")
    print(f"Agent Recovery Rate:          {metrics['recovery_rate']*100:.2f}%")
    print(f"Financial Uplift over Baseline: +{metrics['recovery_uplift']*100:.2f}%")
    print(f"Pending Human Approvals:      {metrics['human_escalations']}")
    print(f"Saved complete batch result to: {output_path}")
    print("=" * 60)
    
    return output_data

if __name__ == "__main__":
    run_batch_evaluation(limit=1000)
