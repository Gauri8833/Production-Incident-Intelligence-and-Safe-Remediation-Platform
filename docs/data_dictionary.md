# Data Dictionary: AIOps Incident Intelligence Platform

## 1. Application Logs (`data/synthetic/application_logs.jsonl`)

| Field | Type | Required | Description | Example |
|---|---|---|---|---|
| `timestamp` | ISO-8601 String | Yes | UTC timestamp when the log event occurred | `2026-10-01T10:20:00Z` |
| `service_name` | String | Yes | Originating microservice (`api_gateway`, `order_service`, `payment_service`, `database`) | `payment_service` |
| `level` | String | Yes | Severity level of the log (`INFO`, `WARN`, `WARNING`, `ERROR`, `CRITICAL`) | `ERROR` |
| `message` | String | Yes | Free-form technical message body | `database connection timeout` |
| `trace_id` | String | No | Distributed tracing identifier across service calls | `trace-a1b2c3d4` |
| `host` | String | No | Server hostname where container or service runs | `host-app-01` |
| `environment` | String | No | Deployment environment (`production`, `staging`) | `production` |
| `scenario` | String | No | Ground-truth simulation scenario for benchmark evaluation | `database_failure` |

---

## 2. Telemetry Metrics (`data/synthetic/metrics.csv`)

| Field | Type | Required | Description | Example |
|---|---|---|---|---|
| `timestamp` | ISO-8601 String | Yes | Measurement interval timestamp (1-minute granularity) | `2026-10-01T10:20:00Z` |
| `service_name` | String | Yes | Microservice emitting the metric | `database` |
| `metric_name` | String | Yes | Name of measured performance indicator | `database_connections_percent` |
| `metric_value` | Float | Yes | Numerical measurement value | `98.4` |
| `scenario` | String | No | Ground-truth label for evaluation | `database_failure` |

### Supported Metric Names:
- `api_latency_ms`: P95 API response time in milliseconds (Baseline: 40-80ms, Anomaly: >500ms).
- `error_rate_percent`: Percentage of failed requests 0.0% to 100.0% (Baseline: <1%, Anomaly: >10%).
- `request_count`: Throughput in requests per minute (Baseline: 100-350 req/min).
- `cpu_percent`: CPU utilization percentage 0.0% to 100.0% (Baseline: 25-45%, Anomaly: >80%).
- `memory_percent`: Resident memory utilization 0.0% to 100.0% (Baseline: 30-60%, Anomaly: >85%).
- `database_connections_percent`: Ratio of active connections to pool ceiling (Baseline: 20-45%, Anomaly: >90%).

---

## 3. Alerts (`alerts` table / records)

| Field | Type | Description |
|---|---|---|
| `id` | String | Unique alert identifier (`ALT-xxxx`) |
| `timestamp` | ISO-8601 String | Time alert was triggered |
| `service_name` | String | Service associated with anomaly or error |
| `alert_type` | String | Category (e.g. `metric_anomaly`, `log_error`) |
| `severity` | String | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` |
| `description` | String | Human-readable explanation of threshold breach |
| `status` | String | Lifecycle status (`OPEN`, `RESOLVED`, `GROUPED`) |

---

## 4. Incidents (`incidents` table / records)

| Field | Type | Description |
|---|---|---|
| `incident_id` | String | Unique incident identifier (`INC-xxxx`) |
| `created_at` | ISO-8601 String | Timestamp when incident was correlated |
| `updated_at` | ISO-8601 String | Last modification timestamp |
| `severity` | String | Highest severity amongst correlated alerts |
| `status` | String | `NEW`, `INVESTIGATING`, `PENDING_APPROVAL`, `MITIGATED`, `RESOLVED`, `CLOSED` |
| `affected_services` | List[String] | Array of impacted services |
| `summary` | String | Synthesized title describing the incident |
| `related_alerts` | List[String] | IDs of grouped alerts |
| `start_time` | ISO-8601 String | Earliest alert timestamp |
| `end_time` | ISO-8601 String | Latest alert timestamp |
