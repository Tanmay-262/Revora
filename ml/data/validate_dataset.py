import os
import json
import pandas as pd
import numpy as np

def validate_dataset(dataset_path="ml/data/payments_dataset.csv"):
    """
    Validates synthetic dataset quality, integrity, and assumption adherence.
    Fails loudly with detailed assertions if critical assumptions are violated.
    """
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset file not found at: {dataset_path}")
        
    df = pd.read_csv(dataset_path)
    report = {
        "status": "PASSED",
        "total_records": len(df),
        "checks": {}
    }
    
    # Check 1: Record count
    if len(df) < 10000:
        report["status"] = "FAILED"
        report["checks"]["record_count"] = f"FAILED: Found {len(df)} records, expected >= 10,000"
    else:
        report["checks"]["record_count"] = f"PASSED: {len(df)} records"
        
    # Check 2: Missing values
    missing = df.isnull().sum().to_dict()
    total_missing = sum(missing.values())
    if total_missing > 0:
        report["status"] = "FAILED"
        report["checks"]["missing_values"] = f"FAILED: {total_missing} null values found: {missing}"
    else:
        report["checks"]["missing_values"] = "PASSED: Zero null values"
        
    # Check 3: Duplicate payment IDs
    duplicate_ids = df["payment_id"].duplicated().sum()
    if duplicate_ids > 0:
        report["status"] = "FAILED"
        report["checks"]["duplicate_ids"] = f"FAILED: {duplicate_ids} duplicate payment IDs"
    else:
        report["checks"]["duplicate_ids"] = "PASSED: All payment IDs are unique"
        
    # Check 4: Valid amounts & positive numerical fields
    invalid_amounts = (df["amount"] <= 0).sum()
    if invalid_amounts > 0:
        report["status"] = "FAILED"
        report["checks"]["amounts"] = f"FAILED: {invalid_amounts} non-positive amounts"
    else:
        report["checks"]["amounts"] = f"PASSED: Amounts range from INR {df['amount'].min():.2f} to INR {df['amount'].max():.2f}"
        
    # Check 5: Categorical domains
    valid_pms = {"upi", "card", "netbanking", "wallet"}
    invalid_pms = set(df["payment_method"]) - valid_pms
    if invalid_pms:
        report["status"] = "FAILED"
        report["checks"]["payment_methods"] = f"FAILED: Invalid payment methods {invalid_pms}"
    else:
        report["checks"]["payment_methods"] = "PASSED: All payment methods valid"
        
    valid_fclasses = {"TEMPORARY_BANK_FAILURE", "PAYMENT_METHOD_FAILURE", "CUSTOMER_ABANDONMENT", "INSUFFICIENT_FUNDS", "UNKNOWN"}
    invalid_fclasses = set(df["failure_class"]) - valid_fclasses
    if invalid_fclasses:
        report["status"] = "FAILED"
        report["checks"]["failure_classes"] = f"FAILED: Invalid failure classes {invalid_fclasses}"
    else:
        report["checks"]["failure_classes"] = "PASSED: All failure classes valid"
        
    # Check 6: Opt-out logic enforcement
    opted_out_recovered = df[(df["customer_opted_out"] == 1) & (df["recovered"] == 1)].shape[0]
    if opted_out_recovered > 0:
        report["status"] = "FAILED"
        report["checks"]["opt_out_rule"] = f"FAILED: {opted_out_recovered} opted-out customers were marked recovered"
    else:
        report["checks"]["opt_out_rule"] = "PASSED: Opt-out customers strictly have 0 recovery rate"
        
    # Check 7: Class imbalance check
    rec_rate = df["recovered"].mean()
    if rec_rate < 0.10 or rec_rate > 0.90:
        report["status"] = "FAILED"
        report["checks"]["class_imbalance"] = f"FAILED: Extreme class imbalance detected ({rec_rate*100:.1f}%)"
    else:
        report["checks"]["class_imbalance"] = f"PASSED: Ground-truth recovery rate is balanced at {rec_rate*100:.2f}%"
        
    report_path = os.path.join(os.path.dirname(dataset_path), "validation_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
        
    if report["status"] == "FAILED":
        raise ValueError(f"Dataset Validation FAILED! Check report at: {report_path}")
        
    print(f"[SUCCESS] Dataset Validation PASSED! Report saved at: {report_path}")
    return report

if __name__ == "__main__":
    validate_dataset()
