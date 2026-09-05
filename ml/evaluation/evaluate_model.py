import os
import json
import joblib
import pandas as pd
import numpy as np

from sklearn.metrics import (
    precision_score, recall_score, f1_score,
    roc_auc_score, precision_recall_curve, auc,
    confusion_matrix
)

def evaluate_on_held_out_test(
    model_path="ml/artifacts/model.joblib",
    test_set_path="ml/evaluation/held_out_test_set.csv",
    output_metrics_path="evaluation/model_metrics.json"
):
    """
    Evaluates trained recovery model on held-out test set.
    Generates precision, recall, f1, roc_auc, pr_auc, and confusion matrix.
    """
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model artifact not found at {model_path}")
    if not os.path.exists(test_set_path):
        raise FileNotFoundError(f"Held out test set not found at {test_set_path}")
        
    pipeline = joblib.load(model_path)
    test_df = pd.read_csv(test_set_path)
    
    y_test = test_df["recovered"]
    X_test = test_df.drop(columns=["recovered"])
    
    y_probs = pipeline.predict_proba(X_test)[:, 1]
    y_preds = (y_probs >= 0.5).astype(int)
    
    precision = precision_score(y_test, y_preds)
    recall = recall_score(y_test, y_preds)
    f1 = f1_score(y_test, y_preds)
    roc_auc = roc_auc_score(y_test, y_probs)
    
    precisions_curve, recalls_curve, _ = precision_recall_curve(y_test, y_probs)
    pr_auc = auc(recalls_curve, precisions_curve)
    
    cm = confusion_matrix(y_test, y_preds).tolist() # [[TN, FP], [FN, TP]]
    
    meta_path = "ml/artifacts/model_meta.json"
    model_name = "Unknown"
    if os.path.exists(meta_path):
        with open(meta_path, "r") as f:
            meta = json.load(f)
            model_name = meta.get("model_name", "Unknown")
            
    metrics = {
        "model_name": model_name,
        "test_sample_count": len(test_df),
        "precision": float(round(precision, 4)),
        "recall": float(round(recall, 4)),
        "f1_score": float(round(f1, 4)),
        "roc_auc": float(round(roc_auc, 4)),
        "pr_auc": float(round(pr_auc, 4)),
        "confusion_matrix": {
            "true_negatives": cm[0][0],
            "false_positives": cm[0][1],
            "false_negatives": cm[1][0],
            "true_positives": cm[1][1]
        }
    }
    
    os.makedirs(os.path.dirname(output_metrics_path), exist_ok=True)
    with open(output_metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
        
    print("=" * 60)
    print(f"HELD-OUT TEST SET EVALUATION ({model_name})")
    print("=" * 60)
    print(f"Precision: {precision:.4f}")
    print(f"Recall:    {recall:.4f}")
    print(f"F1-Score:  {f1:.4f}")
    print(f"ROC-AUC:   {roc_auc:.4f}")
    print(f"PR-AUC:    {pr_auc:.4f}")
    print(f"Confusion Matrix: TN={cm[0][0]}, FP={cm[0][1]}, FN={cm[1][0]}, TP={cm[1][1]}")
    print(f"Saved machine-readable metrics to: {output_metrics_path}")
    print("=" * 60)
    return metrics

if __name__ == "__main__":
    evaluate_on_held_out_test()
