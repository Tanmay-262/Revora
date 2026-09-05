import os
import json
import joblib
import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import roc_auc_score, f1_score, precision_score, recall_score

def train_and_select_model(dataset_path="ml/data/payments_dataset.csv", artifact_dir="ml/artifacts"):
    """
    Trains and evaluates ML model candidates for P(recovered).
    Uses 70% train, 15% val, 15% held-out test split.
    Saves best model pipeline to ml/artifacts/.
    """
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset not found at {dataset_path}")
        
    df = pd.read_csv(dataset_path)
    
    # Target variable
    y = df["recovered"]
    
    # Feature columns (avoiding data leakage: excluding recovery_time, ground_truth_probability, recovery_intervention)
    feature_cols = [
        "amount", "cart_value", "payment_method", "bank", "attempt_number",
        "previous_failures", "customer_age_days", "customer_success_rate",
        "payment_success_rate", "device_type", "failure_code", "failure_class",
        "checkout_duration", "is_subscription", "customer_opted_out",
        "historical_recovery_rate", "bank_failure_rate", "hour_of_day", "day_of_week"
    ]
    
    X = df[feature_cols]
    
    # 70% Train, 15% Val, 15% Test
    X_train_val, X_test, y_train_val, y_test = train_test_split(X, y, test_size=0.15, random_state=42, stratify=y)
    X_train, X_val, y_train, y_val = train_test_split(X_train_val, y_train_val, test_size=0.1765, random_state=42, stratify=y_train_val)
    
    # Save held-out test split for strict final evaluation
    test_df = X_test.copy()
    test_df["recovered"] = y_test
    os.makedirs("ml/evaluation", exist_ok=True)
    test_df.to_csv("ml/evaluation/held_out_test_set.csv", index=False)
    
    num_features = [
        "amount", "cart_value", "attempt_number", "previous_failures",
        "customer_age_days", "customer_success_rate", "payment_success_rate",
        "checkout_duration", "historical_recovery_rate", "bank_failure_rate",
        "hour_of_day", "day_of_week"
    ]
    
    cat_features = [
        "payment_method", "bank", "device_type", "failure_code",
        "failure_class", "is_subscription", "customer_opted_out"
    ]
    
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), num_features),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_features)
        ]
    )
    
    # Candidate models
    candidates = {
        "LogisticRegression": LogisticRegression(max_iter=1000, random_state=42),
        "RandomForest": RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42),
        "XGBoost": XGBClassifier(n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42, eval_metric="logloss")
    }
    
    best_name = None
    best_val_auc = -1.0
    best_pipeline = None
    results = {}
    
    # Fit preprocessor on training data only
    X_train_trans = preprocessor.fit_transform(X_train)
    X_val_trans = preprocessor.transform(X_val)
    
    for name, model in candidates.items():
        model.fit(X_train_trans, y_train)
        val_preds_prob = model.predict_proba(X_val_trans)[:, 1]
        val_preds = (val_preds_prob >= 0.5).astype(int)
        
        auc = roc_auc_score(y_val, val_preds_prob)
        f1 = f1_score(y_val, val_preds)
        prec = precision_score(y_val, val_preds)
        rec = recall_score(y_val, val_preds)
        
        results[name] = {"val_auc": float(auc), "val_f1": float(f1), "val_precision": float(prec), "val_recall": float(rec)}
        print(f"Candidate [{name}] -> Val ROC-AUC: {auc:.4f} | F1: {f1:.4f} | Precision: {prec:.4f} | Recall: {rec:.4f}")
        
        if auc > best_val_auc:
            best_val_auc = auc
            best_name = name
            best_model = model
            
    print(f"\n[SELECTED MODEL]: {best_name} with Val ROC-AUC = {best_val_auc:.4f}")
    
    # Full pipeline with selected model
    pipeline = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("model", best_model)
    ])
    
    os.makedirs(artifact_dir, exist_ok=True)
    model_path = os.path.join(artifact_dir, "model.joblib")
    joblib.dump(pipeline, model_path)
    
    meta = {
        "model_name": best_name,
        "feature_cols": feature_cols,
        "num_features": num_features,
        "cat_features": cat_features,
        "validation_results": results
    }
    with open(os.path.join(artifact_dir, "model_meta.json"), "w") as f:
        json.dump(meta, f, indent=2)
        
    print(f"[SUCCESS] Trained model pipeline saved to: {model_path}")
    return pipeline, meta

if __name__ == "__main__":
    train_and_select_model()
