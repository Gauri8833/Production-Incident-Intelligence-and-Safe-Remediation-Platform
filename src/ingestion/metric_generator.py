import csv
import random
from datetime import datetime, timedelta, timezone
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd

from src.config import SYNTHETIC_DATA_DIR, SERVICES, METRIC_NAMES


def generate_synthetic_metrics(
    output_path: Optional[Path] = None,
    seed: int = 42,
    normal_minutes: int = 60,
    failure_minutes_per_scenario: int = 15,
) -> pd.DataFrame:
    """
    Generates synthetic metrics time series covering normal operations and
    realistic degradation during each failure scenario.
    Outputs: timestamp,service_name,metric_name,metric_value,scenario
    """
    random.seed(seed)
    np.random.seed(seed)

    if output_path is None:
        output_path = SYNTHETIC_DATA_DIR / "metrics.csv"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    start_time = datetime(2026, 10, 1, 8, 0, 0, tzinfo=timezone.utc)
    current_time = start_time
    rows: List[Dict[str, Any]] = []

    def get_service_baseline(service: str, metric: str) -> float:
        baselines = {
            "api_latency_ms": {"api_gateway": 65.0, "order_service": 45.0, "payment_service": 80.0, "database": 15.0},
            "error_rate_percent": {"api_gateway": 0.2, "order_service": 0.1, "payment_service": 0.3, "database": 0.05},
            "request_count": {"api_gateway": 250.0, "order_service": 180.0, "payment_service": 120.0, "database": 350.0},
            "cpu_percent": {"api_gateway": 28.0, "order_service": 35.0, "payment_service": 32.0, "database": 40.0},
            "memory_percent": {"api_gateway": 42.0, "order_service": 50.0, "payment_service": 48.0, "database": 60.0},
            "database_connections_percent": {"api_gateway": 0.0, "order_service": 35.0, "payment_service": 40.0, "database": 38.0},
        }
        return baselines.get(metric, {}).get(service, 20.0)

    def sample_metric_value(service: str, metric: str, scenario: str, elapsed_ratio: float) -> float:
        base = get_service_baseline(service, metric)
        noise = np.random.normal(0, max(0.05 * base, 0.5))

        if scenario == "normal":
            val = max(0.0, base + noise)
            if "percent" in metric:
                val = min(100.0, max(0.0, val))
            return round(float(val), 2)

        # Failure multipliers and overrides
        mult = 1.0
        val = base

        if scenario == "database_failure":
            if service == "database":
                if metric == "database_connections_percent":
                    val = 80.0 + (19.0 * elapsed_ratio) + np.random.normal(0, 1.0)
                elif metric == "cpu_percent":
                    val = 70.0 + (25.0 * elapsed_ratio) + np.random.normal(0, 2.0)
                elif metric == "error_rate_percent":
                    val = 15.0 + (30.0 * elapsed_ratio) + np.random.normal(0, 2.0)
            elif service in ("payment_service", "order_service"):
                if metric == "database_connections_percent":
                    val = 75.0 + (22.0 * elapsed_ratio)
                elif metric == "api_latency_ms":
                    val = base * (3.0 + 8.0 * elapsed_ratio)
                elif metric == "error_rate_percent":
                    val = 10.0 + (40.0 * elapsed_ratio)
            elif service == "api_gateway":
                if metric == "api_latency_ms":
                    val = base * (2.5 + 5.0 * elapsed_ratio)
                elif metric == "error_rate_percent":
                    val = 5.0 + (30.0 * elapsed_ratio)

        elif scenario == "payment_failure":
            if service == "payment_service":
                if metric == "error_rate_percent":
                    val = 45.0 + (45.0 * elapsed_ratio) + np.random.normal(0, 3.0)
                elif metric == "api_latency_ms":
                    val = base * (4.0 + 6.0 * elapsed_ratio)
            elif service in ("order_service", "api_gateway"):
                if metric == "error_rate_percent":
                    val = 15.0 + (35.0 * elapsed_ratio)
                elif metric == "api_latency_ms":
                    val = base * (2.0 + 3.0 * elapsed_ratio)

        elif scenario == "network_failure":
            if metric == "api_latency_ms":
                val = base * (5.0 + 10.0 * elapsed_ratio)
            elif metric == "error_rate_percent":
                val = 20.0 + (50.0 * elapsed_ratio)
            elif metric == "request_count":
                val = max(10.0, base * (1.0 - 0.7 * elapsed_ratio))

        elif scenario == "authentication_failure":
            if service == "api_gateway":
                if metric == "error_rate_percent":
                    val = 30.0 + (40.0 * elapsed_ratio)

        elif scenario == "deployment_failure":
            if service == "order_service":
                if metric == "error_rate_percent":
                    val = 80.0 + np.random.normal(0, 5.0)
                elif metric == "request_count":
                    val = max(5.0, base * 0.1)

        elif scenario == "memory_failure":
            if service == "order_service":
                if metric == "memory_percent":
                    val = 75.0 + (24.0 * elapsed_ratio) + np.random.normal(0, 0.5)
                elif metric == "cpu_percent":
                    val = 85.0 + (12.0 * elapsed_ratio)
                elif metric == "api_latency_ms":
                    val = base * (3.0 + 7.0 * elapsed_ratio)
                elif metric == "error_rate_percent":
                    val = 20.0 + (40.0 * elapsed_ratio)

        elif scenario == "unknown":
            if metric in ("cpu_percent", "error_rate_percent"):
                val = base * (1.8 + np.random.normal(0, 0.5))

        val = val + noise
        if "percent" in metric:
            val = min(100.0, max(0.0, val))
        else:
            val = max(0.0, val)

        return round(float(val), 2)

    # 1. Normal period
    for minute in range(normal_minutes):
        current_time = start_time + timedelta(minutes=minute)
        for svc in SERVICES:
            for metric in METRIC_NAMES:
                val = sample_metric_value(svc, metric, "normal", 0.0)
                rows.append({
                    "timestamp": current_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "service_name": svc,
                    "metric_name": metric,
                    "metric_value": val,
                    "scenario": "normal",
                })

    # 2. Failure scenarios
    scenarios_to_simulate = [
        "database_failure",
        "payment_failure",
        "network_failure",
        "authentication_failure",
        "deployment_failure",
        "memory_failure",
        "unknown",
    ]

    for scn in scenarios_to_simulate:
        # 10 minutes recovery
        interim_start = current_time + timedelta(minutes=1)
        for minute in range(10):
            current_time = interim_start + timedelta(minutes=minute)
            for svc in SERVICES:
                for metric in METRIC_NAMES:
                    val = sample_metric_value(svc, metric, "normal", 0.0)
                    rows.append({
                        "timestamp": current_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "service_name": svc,
                        "metric_name": metric,
                        "metric_value": val,
                        "scenario": "normal",
                    })

        # Failure window
        scenario_start = current_time + timedelta(minutes=1)
        for minute in range(failure_minutes_per_scenario):
            current_time = scenario_start + timedelta(minutes=minute)
            elapsed_ratio = (minute + 1) / failure_minutes_per_scenario
            for svc in SERVICES:
                for metric in METRIC_NAMES:
                    val = sample_metric_value(svc, metric, scn, elapsed_ratio)
                    rows.append({
                        "timestamp": current_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "service_name": svc,
                        "metric_name": metric,
                        "metric_value": val,
                        "scenario": scn,
                    })

    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    print(f"Successfully generated {len(df)} synthetic metrics to {output_path}")
    return df


if __name__ == "__main__":
    generate_synthetic_metrics()
