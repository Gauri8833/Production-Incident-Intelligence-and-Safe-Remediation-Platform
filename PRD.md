# PRD: AIOps Incident Intelligence and Safe Remediation Platform

**Status**: Student prototype / portfolio project  
**Execution**: Free, local-first using Python, Docker, PostgreSQL, and synthetic/public data  

## 1. Product Summary
A platform that helps engineers investigate application failures. It collects logs and metrics, detects abnormal behavior, groups related alerts, ranks probable root causes, searches previous incidents, recommends a safe next action, and records human approval before simulated remediation.

### Core Problem
One production failure can generate hundreds of alerts. Engineers need to answer:
> *What failed, what caused it, what evidence supports that conclusion, and what should we do next?*

### Product Output Workflow
```
Logs + metrics
       ↓
Anomaly detection and log classification
       ↓
Alert grouping
       ↓
Root-cause ranking with evidence
       ↓
Historical incident/RAG search
       ↓
Recommendation
       ↓
Human approval
       ↓
Simulated remediation and audit log
```

## 2. Goals and Scope
### Goals
- Detect anomalies in application metrics.
- Classify technical log messages.
- Group duplicate or related alerts into incidents.
- Rank probable root causes using transparent evidence.
- Retrieve relevant historical incidents and runbooks.
- Recommend safe troubleshooting actions.
- Require approval before any simulated remediation.
- Provide a FastAPI backend and Streamlit dashboard.
- Track model quality and system performance.

### In Scope
- Simulated services: API Gateway, Order Service, Payment Service, and Database.
- Synthetic logs and metrics.
- Public log datasets for additional evaluation.
- Local PostgreSQL / SQLite database.
- Local RAG index using embeddings and vector search.
- Docker deployment.
- MLflow tracking as an advanced phase.

### Out of Scope
- Real company production access.
- Automatic changes to real servers or cloud resources.
- Destructive actions.
- Claims of real business savings without production data.

## 3. Target Users
- **Incident responder**: Understand the current incident quickly.
- **DevOps/SRE engineer**: Investigate alerts and approve actions.
- **Support engineer**: Search historical incidents and runbooks.
- **AI/ML engineer**: Train, evaluate, and deploy the models.

## 4. Main User Workflow
1. Simulated services generate normal logs and metrics.
2. A failure is introduced, such as database connection exhaustion.
3. The ingestion layer validates and stores the events.
4. Anomaly detection identifies abnormal metrics.
5. The log classifier categorizes error messages.
6. The correlation engine groups related alerts.
7. An incident is created with severity and affected services.
8. Root-cause analysis ranks candidate causes.
9. RAG retrieves similar incidents and runbooks.
10. The platform produces a recommendation with evidence and confidence.
11. An engineer approves or rejects the simulated action.
12. The action result and decision are saved in the audit log.
13. The dashboard displays the complete incident lifecycle.

## 5. Architecture
```
Simulated services
 ├── API Gateway
 ├── Order Service
 ├── Payment Service
 └── Database
      │ logs, metrics
      ▼
Ingestion and validation
      ▼
PostgreSQL / local files
 ├── Anomaly detection
 ├── Log classification
 └── Alert grouping
      ▼
 Root-cause ranking
      ▼
 Historical incident RAG
      ▼
 Recommendation service
      ▼
 Approval + simulated remediation
      ▼
 FastAPI backend + dashboard
      ▼
 Audit log
```

## 6. Functional Requirements
- **FR-01: Log Ingestion**: Accept batch JSONL files and API requests (`timestamp`, `service_name`, `level`, `message`, `trace_id`).
- **FR-02: Metric Ingestion**: Accept time-series metrics (`timestamp`, `service_name`, `metric_name`, `metric_value`).
- **FR-03: Anomaly Detection**: Moving average + std dev baseline & Isolation Forest.
- **FR-04: Log Classification**: TF-IDF + Logistic Regression (categories: `normal`, `database_failure`, `payment_failure`, `network_failure`, `authentication_failure`, `deployment_failure`, `memory_failure`, `unknown`).
- **FR-05: Alert Creation and Grouping**: Multi-rule alert grouping and deduplication.
- **FR-06: Incident Management**: Structured incidents with statuses (`NEW`, `INVESTIGATING`, `PENDING_APPROVAL`, `MITIGATED`, `RESOLVED`, `CLOSED`).
- **FR-07: Root-Cause Ranking**: Multi-factor scoring (Timeline 30%, Metric Anomaly 30%, Dependency Graph 20%, Historical Similarity 20%).
- **FR-08: Historical Incident RAG**: Chunked runbooks & incident history with citations & fallback.
- **FR-09: Recommendation & Approval**: Action proposals with required human approval gate.
- **FR-10: FastAPI API**: RESTful API endpoints with Swagger docs.
- **FR-11: Streamlit Dashboard**: Full UI with overview, drill-down, charts, and interactive approval.
