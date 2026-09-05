import os
import pytest
import pandas as pd
from ml.data.generate_dataset import generate_synthetic_dataset
from ml.data.validate_dataset import validate_dataset

def test_generate_and_validate_dataset(tmp_path):
    csv_path = str(tmp_path / "test_payments.csv")
    df = generate_synthetic_dataset(num_records=100, seed=123, output_path=csv_path)
    
    assert len(df) == 100
    assert os.path.exists(csv_path)
    assert "payment_id" in df.columns
    assert "failure_class" in df.columns
    assert "recovered" in df.columns

def test_opt_out_rule_integrity(tmp_path):
    csv_path = str(tmp_path / "test_optout.csv")
    df = generate_synthetic_dataset(num_records=500, seed=999, output_path=csv_path)
    opt_out_recovered = df[(df["customer_opted_out"] == 1) & (df["recovered"] == 1)]
    assert len(opt_out_recovered) == 0, "Opted-out customers must never be recovered"
