import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from pydantic import ValidationError

from src.config import (
    SYNTHETIC_DATA_DIR,
    PROCESSED_DATA_DIR,
    SERVICES,
    METRIC_NAMES,
    LOG_LEVELS,
)
from src.schemas import LogRecord, MetricRecord


class ValidationResult:
    def __init__(self, is_valid: bool, errors: Optional[List[str]] = None):
        self.is_valid = is_valid
        self.errors = errors or []

    def __repr__(self) -> str:
        return f"ValidationResult(is_valid={self.is_valid}, errors={self.errors})"


def validate_log_dict(record: Dict[str, Any]) -> ValidationResult:
    """Validates an incoming log dictionary according to FR-01."""
    errors = []

    # Required fields
    for field in ["timestamp", "service_name", "level", "message"]:
        if field not in record or record[field] is None or str(record[field]).strip() == "":
            errors.append(f"Missing or empty required field: '{field}'")

    if errors:
        return ValidationResult(is_valid=False, errors=errors)

    # Validate timestamp
    try:
        if isinstance(record["timestamp"], str):
            pd.to_datetime(record["timestamp"])
    except Exception as e:
        errors.append(f"Invalid timestamp format: {record['timestamp']} ({e})")

    # Validate service_name
    if record["service_name"] not in SERVICES:
        errors.append(f"Unknown service_name: '{record['service_name']}'. Expected one of {SERVICES}")

    # Validate log level
    level_upper = str(record["level"]).upper()
    if level_upper not in LOG_LEVELS:
        errors.append(f"Unknown log level: '{record['level']}'. Expected one of {LOG_LEVELS}")

    # PII masking (e.g. emails, credit cards, auth tokens)
    # We validate message string exists
    if not isinstance(record["message"], str) or len(record["message"].strip()) == 0:
        errors.append("Log message must be a non-empty string")

    return ValidationResult(is_valid=len(errors) == 0, errors=errors)


def mask_pii(text: str) -> str:
    """Masks sensitive PII patterns in log messages (emails, card numbers, secrets)."""
    # Mask credit card numbers (13-16 digits)
    text = re.sub(r"\b(?:\d{4}[ -]?){3}\d{4}\b", "[CARD_MASKED]", text)
    # Mask email addresses
    text = re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b", "[EMAIL_MASKED]", text)
    # Mask JWT or long hex bearer tokens
    text = re.sub(r"Bearer\s+[A-Za-z0-9\-_.]+", "Bearer [TOKEN_MASKED]", text)
    return text


def validate_metric_dict(record: Dict[str, Any]) -> ValidationResult:
    """Validates an incoming metric record according to FR-02."""
    errors = []

    for field in ["timestamp", "service_name", "metric_name", "metric_value"]:
        if field not in record or record[field] is None or str(record[field]).strip() == "":
            errors.append(f"Missing or empty required field: '{field}'")

    if errors:
        return ValidationResult(is_valid=False, errors=errors)

    # Validate timestamp
    try:
        if isinstance(record["timestamp"], str):
            pd.to_datetime(record["timestamp"])
    except Exception as e:
        errors.append(f"Invalid timestamp format: {record['timestamp']}")

    # Validate service
    if record["service_name"] not in SERVICES:
        errors.append(f"Unknown service_name: '{record['service_name']}'")

    # Validate metric name
    if record["metric_name"] not in METRIC_NAMES:
        errors.append(f"Unknown metric_name: '{record['metric_name']}'")

    # Validate metric value
    try:
        val = float(record["metric_value"])
        if pd.isna(val):
            errors.append("metric_value cannot be NaN")
        if val < 0:
            errors.append(f"metric_value cannot be negative: {val}")
        if "percent" in record["metric_name"] and val > 100.0001:
            errors.append(f"Percentage metric cannot exceed 100%: {val}")
    except (ValueError, TypeError):
        errors.append(f"metric_value must be a valid float: {record.get('metric_value')}")

    return ValidationResult(is_valid=len(errors) == 0, errors=errors)


def clean_and_process_data(
    raw_logs_path: Optional[Path] = None,
    raw_metrics_path: Optional[Path] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Ingests raw synthetic data, validates all records, removes duplicates,
    sorts events chronologically, masks PII, and stores clean outputs.
    """
    if raw_logs_path is None:
        raw_logs_path = SYNTHETIC_DATA_DIR / "application_logs.jsonl"
    if raw_metrics_path is None:
        raw_metrics_path = SYNTHETIC_DATA_DIR / "metrics.csv"

    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Process logs
    valid_logs = []
    seen_log_keys = set()

    with open(raw_logs_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue

            v_res = validate_log_dict(rec)
            if v_res.is_valid:
                # Deduplication key: timestamp + service + message
                key = (rec["timestamp"], rec["service_name"], rec["message"])
                if key not in seen_log_keys:
                    seen_log_keys.add(key)
                    rec["message"] = mask_pii(rec["message"])
                    valid_logs.append(rec)

    df_logs = pd.DataFrame(valid_logs)
    if not df_logs.empty:
        df_logs["parsed_timestamp"] = pd.to_datetime(df_logs["timestamp"])
        df_logs = df_logs.sort_values("parsed_timestamp").drop(columns=["parsed_timestamp"])

    clean_logs_path = PROCESSED_DATA_DIR / "clean_logs.jsonl"
    with open(clean_logs_path, "w", encoding="utf-8") as f:
        for _, row in df_logs.iterrows():
            f.write(json.dumps(row.to_dict()) + "\n")

    # Process metrics
    df_raw_metrics = pd.read_csv(raw_metrics_path)
    valid_metrics = []
    seen_metric_keys = set()

    for rec in df_raw_metrics.to_dict(orient="records"):
        v_res = validate_metric_dict(rec)
        if v_res.is_valid:
            key = (rec["timestamp"], rec["service_name"], rec["metric_name"])
            if key not in seen_metric_keys:
                seen_metric_keys.add(key)
                valid_metrics.append(rec)

    df_metrics = pd.DataFrame(valid_metrics)
    if not df_metrics.empty:
        df_metrics["parsed_timestamp"] = pd.to_datetime(df_metrics["timestamp"])
        df_metrics = df_metrics.sort_values("parsed_timestamp").drop(columns=["parsed_timestamp"])

    clean_metrics_path = PROCESSED_DATA_DIR / "clean_metrics.csv"
    df_metrics.to_csv(clean_metrics_path, index=False)

    print(f"Data validation complete: {len(df_logs)} clean logs, {len(df_metrics)} clean metrics.")
    return df_logs, df_metrics


if __name__ == "__main__":
    clean_and_process_data()
