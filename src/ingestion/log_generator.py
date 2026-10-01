import json
import random
import uuid
from datetime import datetime, timedelta, timezone
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import SYNTHETIC_DATA_DIR, SERVICES

# Domain-specific templates for realistic log messages
LOG_TEMPLATES = {
    "normal": {
        "api_gateway": [
            ("INFO", "GET /api/v1/orders HTTP/1.1 200 OK duration={lat}ms"),
            ("INFO", "POST /api/v1/checkout HTTP/1.1 200 OK duration={lat}ms"),
            ("INFO", "GET /health status=healthy upstream=reachable"),
            ("INFO", "Dispatched request to {target} with trace_id={trace}"),
        ],
        "order_service": [
            ("INFO", "Order ORD-{id} created successfully for customer CUST-{cid}"),
            ("INFO", "Processing order items count={cnt} total_amount=${amt}"),
            ("INFO", "Dispatched payment request for ORD-{id}"),
            ("INFO", "Order state transitioned to PENDING_FULFILLMENT"),
        ],
        "payment_service": [
            ("INFO", "Processing payment charge for transaction TX-{id}"),
            ("INFO", "Payment authorization successful via payment provider"),
            ("INFO", "Transaction TX-{id} recorded in ledger"),
            ("INFO", "Payment receipt dispatched for customer CUST-{cid}"),
        ],
        "database": [
            ("INFO", "SELECT * FROM orders WHERE status='ACTIVE' duration=4ms"),
            ("INFO", "INSERT INTO transactions VALUES (...) completed in 8ms"),
            ("INFO", "Checkpoint complete: wrote 42 buffers in 12ms"),
            ("INFO", "Autovacuum completed on public.orders"),
        ],
    },
    "database_failure": {
        "database": [
            ("CRITICAL", "FATAL: remaining connection slots are reserved for non-replication superuser connections"),
            ("ERROR", "Connection pool exhausted: active_connections=100 max_connections=100"),
            ("ERROR", "PostgreSQL connection timeout: failed to acquire connection after 30000ms"),
            ("ERROR", "deadlock detected in process {pid} query='UPDATE payment_records...'"),
        ],
        "payment_service": [
            ("ERROR", "Database connection pool timeout while acquiring connection for TX-{id}"),
            ("ERROR", "OperationalError: could not connect to server: Connection refused on port 5432"),
            ("ERROR", "Failed to persist transaction TX-{id} due to db connection exhaustion"),
        ],
        "order_service": [
            ("ERROR", "Failed to query order database: connection timeout waiting for pool"),
            ("ERROR", "Database query failed for customer CUST-{cid}: server closed connection unexpectedly"),
        ],
        "api_gateway": [
            ("ERROR", "Upstream order_service returned HTTP 500 Internal Server Error"),
            ("WARN", "High latency observed from order_service: response_time=3200ms"),
        ],
    },
    "payment_failure": {
        "payment_service": [
            ("ERROR", "Payment gateway HTTP 504 Gateway Timeout while contacting processor"),
            ("ERROR", "Payment authorization failed for TX-{id}: 3rd party vendor unreachable"),
            ("CRITICAL", "Payment processor circuit breaker tripped OPEN after 15 consecutive timeouts"),
        ],
        "order_service": [
            ("ERROR", "Payment failed for order ORD-{id}: payment service rejected request"),
            ("WARN", "Order ORD-{id} marked as PAYMENT_FAILED"),
        ],
        "api_gateway": [
            ("ERROR", "POST /api/v1/checkout HTTP/1.1 502 Bad Gateway duration={lat}ms"),
        ],
        "database": [
            ("INFO", "ROLLBACK transaction for TX-{id}"),
        ],
    },
    "network_failure": {
        "api_gateway": [
            ("ERROR", "Connection reset by peer while connecting to order_service:8080"),
            ("ERROR", "DNS resolution timeout for internal domain order.local"),
        ],
        "order_service": [
            ("ERROR", "SocketTimeoutException reading from payment_service:8081"),
            ("ERROR", "Network read timeout after 10000ms"),
        ],
        "payment_service": [
            ("WARN", "TCP handshake delay spike: 1800ms to downstream"),
        ],
        "database": [
            ("WARN", "TCP keepalive timeout on client connection socket"),
        ],
    },
    "authentication_failure": {
        "api_gateway": [
            ("WARN", "Invalid JWT signature received from IP 192.168.1.105"),
            ("WARN", "Authentication failed: token expired at {time}"),
            ("ERROR", "OAuth token introspection endpoint returned HTTP 401 Unauthorized"),
        ],
        "order_service": [
            ("WARN", "Access denied: missing scope 'orders.write'"),
        ],
        "payment_service": [
            ("WARN", "Unauthorized payment attempt without Bearer token"),
        ],
        "database": [
            ("INFO", "User auth audit logged"),
        ],
    },
    "deployment_failure": {
        "order_service": [
            ("CRITICAL", "Flyway schema migration failed: column 'customer_metadata' does not exist in v2.4"),
            ("CRITICAL", "Application bootstrap failed during canary deployment v2.4.0"),
            ("ERROR", "NullPointerException during startup in OrderConfigBean.java:42"),
        ],
        "api_gateway": [
            ("WARN", "Upstream order_service healthy instances dropped to 0/3"),
            ("ERROR", "503 Service Unavailable: no healthy upstream hosts"),
        ],
        "payment_service": [
            ("INFO", "Service healthy"),
        ],
        "database": [
            ("ERROR", "Migration lock table pg_advisory_lock timeout"),
        ],
    },
    "memory_failure": {
        "order_service": [
            ("CRITICAL", "java.lang.OutOfMemoryError: Java heap space"),
            ("ERROR", "Garbage collection overhead limit exceeded: GC took 98% of CPU"),
            ("CRITICAL", "Process killed by Linux OOM killer: pid=4921 invoked oom-killer"),
        ],
        "payment_service": [
            ("WARN", "Memory allocation threshold exceeded: 96% of RSS heap used"),
        ],
        "api_gateway": [
            ("WARN", "Upstream order_service unresponsive: socket hanging"),
        ],
        "database": [
            ("INFO", "Active connections 32"),
        ],
    },
    "unknown": {
        "order_service": [
            ("ERROR", "Internal system anomaly: unrecognized error code err_0x99A"),
            ("ERROR", "Arbitrary unhandled worker state encountered: state=corrupt"),
        ],
        "payment_service": [
            ("ERROR", "Unexpected panic in native worker routine"),
        ],
        "api_gateway": [
            ("ERROR", "Unknown routing state for inbound packet"),
        ],
        "database": [
            ("WARN", "Uncategorized server warning code 4009"),
        ],
    },
}


def generate_single_log(
    timestamp: datetime,
    service_name: str,
    scenario: str,
    trace_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Generates a single structured log dictionary following the PRD schema."""
    if trace_id is None:
        trace_id = f"trace-{uuid.uuid4().hex[:8]}"

    scenario_bucket = LOG_TEMPLATES.get(scenario, LOG_TEMPLATES["normal"])
    templates = scenario_bucket.get(service_name, LOG_TEMPLATES["normal"].get(service_name, [("INFO", "Operational event")]))

    level, tmpl = random.choice(templates)
    message = tmpl.format(
        lat=random.randint(15, 250) if scenario == "normal" else random.randint(1500, 8000),
        id=random.randint(1000, 9999),
        cid=random.randint(100, 999),
        cnt=random.randint(1, 5),
        amt=round(random.uniform(10.0, 500.0), 2),
        pid=random.randint(1000, 8000),
        target=random.choice(["order_service", "payment_service"]),
        trace=trace_id,
        time=timestamp.isoformat(),
    )

    return {
        "timestamp": timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "service_name": service_name,
        "level": level,
        "message": message,
        "trace_id": trace_id,
        "scenario": scenario,
    }


def generate_synthetic_logs(
    output_path: Optional[Path] = None,
    seed: int = 42,
    normal_minutes: int = 60,
    failure_minutes_per_scenario: int = 15,
) -> List[Dict[str, Any]]:
    """
    Generates a full synthetic log dataset spanning normal operations
    and each failure scenario, strictly adhering to reproducible random seeds.
    """
    random.seed(seed)
    if output_path is None:
        output_path = SYNTHETIC_DATA_DIR / "application_logs.jsonl"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    start_time = datetime(2026, 10, 1, 8, 0, 0, tzinfo=timezone.utc)
    current_time = start_time
    logs: List[Dict[str, Any]] = []

    # 1. Normal period (e.g. 60 minutes)
    for minute in range(normal_minutes):
        current_time = start_time + timedelta(minutes=minute)
        # Average 5-10 logs per minute across services
        log_count = random.randint(5, 10)
        for _ in range(log_count):
            svc = random.choice(SERVICES)
            log = generate_single_log(
                timestamp=current_time + timedelta(seconds=random.randint(0, 59)),
                service_name=svc,
                scenario="normal",
            )
            logs.append(log)

    # 2. Failure scenarios (database, payment, network, auth, deployment, memory, unknown)
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
        # 10 minutes of recovery / normal before next incident
        interim_start = current_time + timedelta(minutes=5)
        for minute in range(10):
            current_time = interim_start + timedelta(minutes=minute)
            for _ in range(random.randint(4, 8)):
                svc = random.choice(SERVICES)
                logs.append(generate_single_log(
                    timestamp=current_time + timedelta(seconds=random.randint(0, 59)),
                    service_name=svc,
                    scenario="normal",
                ))

        # Failure window
        scenario_start = current_time + timedelta(minutes=1)
        for minute in range(failure_minutes_per_scenario):
            current_time = scenario_start + timedelta(minutes=minute)
            # Heavy burst of logs during failure
            log_count = random.randint(15, 25)
            # Primary service affected
            primary_svc = "database" if "database" in scn else (
                "payment_service" if "payment" in scn else (
                    "order_service" if "memory" in scn or "deployment" in scn else random.choice(SERVICES)
                )
            )
            for _ in range(log_count):
                # 70% primary service, 30% cascading services
                svc = primary_svc if random.random() < 0.70 else random.choice(SERVICES)
                # Some logs are errors from failure, some are background traffic
                is_err = random.random() < 0.80
                chosen_scn = scn if is_err else "normal"
                logs.append(generate_single_log(
                    timestamp=current_time + timedelta(seconds=random.randint(0, 59)),
                    service_name=svc,
                    scenario=chosen_scn,
                ))

    # Sort logs chronologically
    logs.sort(key=lambda x: x["timestamp"])

    # Write out to JSONL
    with open(output_path, "w", encoding="utf-8") as f:
        for entry in logs:
            f.write(json.dumps(entry) + "\n")

    print(f"Successfully generated {len(logs)} synthetic logs to {output_path}")
    return logs


if __name__ == "__main__":
    generate_synthetic_logs()
