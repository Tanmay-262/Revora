import os
import pytest
import pandas as pd
from ml.models.train_model import train_and_select_model
from ml.evaluation.evaluate_model import evaluate_on_held_out_test

def test_model_training_and_artifacts(tmp_path):
    # Train pipeline
    pipeline, meta = train_and_select_model(
        dataset_path="ml/data/payments_dataset.csv",
        artifact_dir=str(tmp_path / "artifacts")
    )
    assert pipeline is not None
    assert os.path.exists(str(tmp_path / "artifacts" / "model.joblib"))
    assert "model_name" in meta

def test_model_evaluation_report(tmp_path):
    metrics = evaluate_on_held_out_test(
        model_path="ml/artifacts/model.joblib",
        test_set_path="ml/evaluation/held_out_test_set.csv",
        output_metrics_path=str(tmp_path / "model_metrics.json")
    )
    assert metrics["roc_auc"] > 0.50
    assert metrics["precision"] > 0.0
    assert metrics["recall"] > 0.0
    assert "confusion_matrix" in metrics
