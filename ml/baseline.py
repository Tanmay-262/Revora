import os
import json
import numpy as np
import pandas as pd

def run_baseline_simulation(dataset_path="ml/data/payments_dataset.csv", output_path="evaluation/baseline_metrics.json"):
    """
    Implements a traditional baseline strategy:
    "For every failed payment (where customer hasn't opted out), retry once immediately via RETRY_LATER."
    
    Measures:
    - Number of failed payments
    - Total revenue at risk
    - Total recovered revenue
    - Baseline Recovery Rate
    - Total interventions executed
    - Unnecessary / wasteful interventions
    """
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset not found at {dataset_path}")
        
    df = pd.read_csv(dataset_path)
    
    total_failed_payments = len(df)
    total_revenue_at_risk = float(df["amount"].sum())
    
    # Baseline logic:
    # If customer opted out -> NO intervention, 0 recovery
    # If customer did NOT opt out -> attempt 1 immediate retry ("RETRY_LATER")
    # Baseline recovery success happens if ground_truth_probability is reasonable and failure_class is TEMPORARY_BANK_FAILURE or INSUFFICIENT_FUNDS
    
    interventions_count = 0
    recovered_revenue = 0.0
    recovered_count = 0
    unnecessary_interventions = 0
    
    # Deterministic simulation using ground-truth attributes
    for _, row in df.iterrows():
        if row["customer_opted_out"] == 1:
            continue
            
        interventions_count += 1
        
        # In baseline, retrying works mainly if the failure was temporary bank error or high customer history
        # Baseline probability of success is lower because it blindly retries without root cause intervention matching
        p_baseline = 0.0
        if row["failure_class"] == "TEMPORARY_BANK_FAILURE":
            p_baseline = row["ground_truth_probability"] * 0.75  # Blind immediate retry is sub-optimal
        elif row["failure_class"] == "INSUFFICIENT_FUNDS":
            p_baseline = row["ground_truth_probability"] * 0.30
        elif row["failure_class"] == "PAYMENT_METHOD_FAILURE":
            p_baseline = row["ground_truth_probability"] * 0.10  # Retrying an expired card almost always fails
        elif row["failure_class"] == "CUSTOMER_ABANDONMENT":
            p_baseline = row["ground_truth_probability"] * 0.15  # Retrying without sending link/reminder rarely works
        else:
            p_baseline = 0.05
            
        # Seeded deterministic outcome per row
        row_seed = int(row["payment_id"].split("_")[1]) % 100000
        rng = np.random.RandomState(row_seed)
        
        is_recovered = rng.rand() < p_baseline
        if is_recovered:
            recovered_count += 1
            recovered_revenue += float(row["amount"])
        else:
            # Baseline performed an intervention that failed completely (wasteful friction)
            unnecessary_interventions += 1
            
    recovery_rate = recovered_revenue / total_revenue_at_risk if total_revenue_at_risk > 0 else 0.0
    
    metrics = {
        "strategy_name": "BASELINE_BLIND_RETRY_ONCE",
        "total_failed_payments": total_failed_payments,
        "total_revenue_at_risk": total_revenue_at_risk,
        "total_recovered_revenue": float(round(recovered_revenue, 2)),
        "recovered_count": recovered_count,
        "recovery_rate": float(round(recovery_rate, 4)),
        "total_interventions": interventions_count,
        "successful_interventions": recovered_count,
        "unnecessary_interventions": unnecessary_interventions,
        "intervention_efficiency": float(round(recovered_count / interventions_count, 4)) if interventions_count > 0 else 0.0
    }
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(metrics, f, indent=2)
        
    print(f"[SUCCESS] Baseline simulation completed.")
    print(f"Baseline Recovery Rate: {metrics['recovery_rate']*100:.2f}% | Revenue Recovered: INR {metrics['total_recovered_revenue']:,.2f} of INR {metrics['total_revenue_at_risk']:,.2f}")
    return metrics

if __name__ == "__main__":
    run_baseline_simulation()
