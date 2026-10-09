import json
from pathlib import Path
import pandas as pd
import pytest

from src.config import SYNTHETIC_DATA_DIR, SERVICES, METRIC_NAMES


def test_phase1_logs_file_exists():
    log_file = SYNTHETIC_DATA_DIR / "application_logs.jsonl"
    assert log_file.exists(), "application_logs.jsonl does not exist"
    assert log_file.stat().st_size > 0, "application_logs.jsonl is empty"


def test_phase1_logs_schema_and_scenarios():
    log_file = SYNTHETIC_DATA_DIR / "application_logs.jsonl"
    records = []
    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    assert len(records) > 0, "No log records found"

    # Check required fields
    required_fields = ["timestamp", "service_name", "level", "message"]
    scenarios_found = set()
    services_found = set()

    for r in records:
        for field in required_fields:
            assert field in r, f"Missing required field {field} in log record"
        services_found.add(r["service_name"])
        if "scenario" in r:
            scenarios_found.add(r["scenario"])

    # Check that services and scenarios exist
    assert "database" in services_found or "order_service" in services_found
    assert "normal" in scenarios_found
    assert any("failure" in s for s in scenarios_found)


def test_phase1_metrics_file_exists():
    metric_file = SYNTHETIC_DATA_DIR / "metrics.csv"
    assert metric_file.exists(), "metrics.csv does not exist"
    assert metric_file.stat().st_size > 0, "metrics.csv is empty"


def test_phase1_metrics_schema_and_values():
    metric_file = SYNTHETIC_DATA_DIR / "metrics.csv"
    df = pd.read_csv(metric_file)

    # Required columns
    expected_cols = ["timestamp", "service_name", "metric_name", "metric_value", "scenario"]
    for col in expected_cols:
        assert col in df.columns, f"Missing column {col} in metrics.csv"

    # Validate timestamps
    pd.to_datetime(df["timestamp"].iloc[:100])

    # Check scenarios
    scenarios = set(df["scenario"].unique())
    assert "normal" in scenarios
    assert "database_failure" in scenarios

    # Check metrics
    metric_names = set(df["metric_name"].unique())
    assert "database_connections_percent" in metric_names
    assert "api_latency_ms" in metric_names
