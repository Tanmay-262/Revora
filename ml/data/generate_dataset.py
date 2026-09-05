import os
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def generate_synthetic_dataset(num_records=10000, seed=42, output_path="ml/data/payments_dataset.csv"):
    """
    Generates a realistic synthetic dataset of 10,000+ failed payment transactions.
    Creates structured relationships between features and ground-truth recovery outcomes.
    """
    np.random.seed(seed)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 1. Base identifiers & timestamps
    start_date = datetime(2026, 1, 1)
    random_minutes = np.random.randint(0, 60 * 24 * 60, size=num_records)
    timestamps = [start_date + timedelta(minutes=int(m)) for m in random_minutes]
    timestamps.sort()
    
    payment_ids = [f"pay_{i+100000:06d}" for i in range(num_records)]
    customer_ids = [f"cust_{np.random.randint(1000, 4000):04d}" for _ in range(num_records)]
    merchant_id = "merch_razorpay_buildathon"
    currency = "INR"
    
    # 2. Payment methods & Banks
    payment_methods = ["upi", "card", "netbanking", "wallet"]
    pm_probs = [0.55, 0.25, 0.15, 0.05]
    chosen_pms = np.random.choice(payment_methods, size=num_records, p=pm_probs)
    
    banks = ["HDFC", "ICICI", "SBI", "AXIS", "KOTAK", "NONE"]
    bank_probs = [0.30, 0.25, 0.20, 0.15, 0.08, 0.02]
    chosen_banks = np.random.choice(banks, size=num_records, p=bank_probs)
    
    # 3. Transaction values & Subscriptions
    # Bimodal amount distribution (small e-commerce/subscription ₹200-₹2000, high value ₹5000-₹50000)
    is_high_value = np.random.rand(num_records) < 0.15
    amounts = np.where(
        is_high_value,
        np.random.uniform(10000, 50000, size=num_records),
        np.random.exponential(scale=1500, size=num_records) + 199
    ).round(2)
    
    cart_values = (amounts * np.random.uniform(1.0, 1.2, size=num_records)).round(2)
    is_subscription = (np.random.rand(num_records) < 0.25).astype(int)
    
    # 4. Customer profiles & Behavior
    customer_age_days = np.random.exponential(scale=180, size=num_records).astype(int) + 1
    customer_success_rate = np.clip(np.random.beta(a=8, b=2, size=num_records), 0.10, 0.99).round(4)
    payment_success_rate = np.clip(np.random.beta(a=7, b=3, size=num_records), 0.15, 0.98).round(4)
    
    attempt_number = np.random.choice([1, 2, 3], size=num_records, p=[0.70, 0.22, 0.08])
    previous_failures = np.random.poisson(lam=0.5, size=num_records)
    
    device_type = np.random.choice(["mobile_android", "mobile_ios", "desktop", "mobile_web"], size=num_records, p=[0.60, 0.20, 0.12, 0.08])
    checkout_duration = np.random.exponential(scale=45, size=num_records).astype(int) + 5
    
    # Opt out flag (~3% hard opt out)
    customer_opted_out = (np.random.rand(num_records) < 0.03).astype(int)
    
    # Bank failure rate spike simulation (simulating temporary bank downtime window)
    bank_failure_rates = np.random.beta(a=1.5, b=20, size=num_records).round(4)
    # Simulate downtime spike for SBI / HDFC periodically
    for idx, ts in enumerate(timestamps):
        if chosen_banks[idx] in ["SBI", "HDFC"] and (ts.hour in [14, 15, 20]):
            bank_failure_rates[idx] = round(float(np.random.uniform(0.40, 0.85)), 4)
            
    historical_recovery_rate = np.clip(np.random.beta(a=5, b=5, size=num_records), 0.05, 0.95).round(4)
    
    # 5. Failure codes & failure classes
    # Failure class distribution:
    # 1. TEMPORARY_BANK_FAILURE (35%)
    # 2. PAYMENT_METHOD_FAILURE (25%)
    # 3. CUSTOMER_ABANDONMENT (20%)
    # 4. INSUFFICIENT_FUNDS (15%)
    # 5. UNKNOWN (5%)
    
    failure_classes = ["TEMPORARY_BANK_FAILURE", "PAYMENT_METHOD_FAILURE", "CUSTOMER_ABANDONMENT", "INSUFFICIENT_FUNDS", "UNKNOWN"]
    f_class_probs = [0.35, 0.25, 0.20, 0.15, 0.05]
    chosen_failure_classes = np.random.choice(failure_classes, size=num_records, p=f_class_probs)
    
    code_map = {
        "TEMPORARY_BANK_FAILURE": ["BAD_REQUEST_GATEWAY_TIMEOUT", "BANK_SERVER_DOWN", "NETWORK_ERROR"],
        "PAYMENT_METHOD_FAILURE": ["CARD_EXPIRED", "UPI_PIN_INVALID", "METHOD_NOT_SUPPORTED"],
        "CUSTOMER_ABANDONMENT": ["CHECKOUT_TIMEOUT", "OTP_NOT_ENTERED", "USER_DROPPED_OFF"],
        "INSUFFICIENT_FUNDS": ["INSUFFICIENT_FUNDS", "TRANSACTION_LIMIT_EXCEEDED"],
        "UNKNOWN": ["UNKNOWN_ERROR", "INTERNAL_SERVER_ERROR"]
    }
    
    failure_codes = [np.random.choice(code_map[fc]) for fc in chosen_failure_classes]
    
    # 6. Realistic Ground Truth Recovery Calculation
    # Recovery likelihood depends on failure class, customer history, bank state, attempt count, and opt-out state
    
    recovery_prob = np.zeros(num_records)
    best_intervention = []
    
    for i in range(num_records):
        if customer_opted_out[i]:
            recovery_prob[i] = 0.0
            best_intervention.append("NO_ACTION")
            continue
            
        fc = chosen_failure_classes[i]
        cust_score = customer_success_rate[i]
        att = attempt_number[i]
        bank_fail = bank_failure_rates[i]
        amt = amounts[i]
        
        if att >= 3:
            # High attempt count reduces recovery probability significantly
            base_p = 0.15
        else:
            base_p = 0.50
            
        if fc == "TEMPORARY_BANK_FAILURE":
            # High bank failure rate means temporary issue -> high recovery if retried later
            p = base_p + 0.35 * cust_score + (0.15 if bank_fail > 0.3 else 0.05)
            interv = "RETRY_LATER"
        elif fc == "PAYMENT_METHOD_FAILURE":
            # Switching payment method yields high recovery
            p = base_p + 0.30 * cust_score + 0.10
            interv = "ALTERNATIVE_PAYMENT_METHOD"
        elif fc == "CUSTOMER_ABANDONMENT":
            # Sending payment link reminding customer yields high recovery
            p = base_p + 0.25 * cust_score + (0.15 if is_subscription[i] else 0.05)
            interv = "SEND_PAYMENT_LINK"
        elif fc == "INSUFFICIENT_FUNDS":
            # Moderate recovery probability
            p = 0.20 + 0.20 * cust_score
            interv = "RETRY_LATER"
        else: # UNKNOWN
            p = 0.25 + 0.15 * cust_score
            interv = "HUMAN_REVIEW"
            
        # Large amounts require careful handling / lower unprompted recovery
        if amt > 20000:
            p *= 0.85
            
        p = float(np.clip(p, 0.02, 0.95))
        recovery_prob[i] = p
        best_intervention.append(interv)
        
    # Sample ground-truth recovered status (1 or 0) based on recovery_prob
    recovered = (np.random.rand(num_records) < recovery_prob).astype(int)
    
    # Recovery time (in minutes) if recovered
    recovery_time = np.where(
        recovered == 1,
        np.random.exponential(scale=120, size=num_records).astype(int) + 5,
        0
    )
    
    df = pd.DataFrame({
        "payment_id": payment_ids,
        "customer_id": customer_ids,
        "merchant_id": merchant_id,
        "amount": amounts,
        "currency": currency,
        "payment_method": chosen_pms,
        "bank": chosen_banks,
        "timestamp": [ts.isoformat() for ts in timestamps],
        "hour_of_day": [ts.hour for ts in timestamps],
        "day_of_week": [ts.weekday() for ts in timestamps],
        "attempt_number": attempt_number,
        "previous_failures": previous_failures,
        "customer_age_days": customer_age_days,
        "customer_success_rate": customer_success_rate,
        "payment_success_rate": payment_success_rate,
        "device_type": device_type,
        "failure_code": failure_codes,
        "failure_class": chosen_failure_classes,
        "checkout_duration": checkout_duration,
        "cart_value": cart_values,
        "is_subscription": is_subscription,
        "customer_opted_out": customer_opted_out,
        "historical_recovery_rate": historical_recovery_rate,
        "bank_failure_rate": bank_failure_rates,
        "recovered": recovered,
        "ground_truth_probability": recovery_prob.round(4),
        "recovery_intervention": best_intervention,
        "recovery_time": recovery_time
    })
    
    df.to_csv(output_path, index=False)
    
    summary = {
        "total_records": len(df),
        "total_revenue_at_risk": float(df["amount"].sum()),
        "total_recovered_revenue": float(df[df["recovered"] == 1]["amount"].sum()),
        "overall_recovery_rate": float(df["recovered"].mean()),
        "failure_class_counts": df["failure_class"].value_counts().to_dict(),
        "intervention_counts": df["recovery_intervention"].value_counts().to_dict(),
        "opted_out_count": int(df["customer_opted_out"].sum())
    }
    
    summary_path = os.path.join(os.path.dirname(output_path), "dataset_summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
        
    print(f"[SUCCESS] Synthetic dataset with {len(df)} records generated at: {output_path}")
    print(f"Summary: Total At Risk: INR {summary['total_revenue_at_risk']:,.2f} | Recovered: INR {summary['total_recovered_revenue']:,.2f} ({summary['overall_recovery_rate']*100:.1f}%)")
    return df

if __name__ == "__main__":
    generate_synthetic_dataset()
