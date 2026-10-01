# AIOps Incident Intelligence and Safe Remediation Platform

An end-to-end AIOps platform that accelerates incident investigation and safe remediation across microservice environments. The platform ingests telemetry (logs and metrics), detects metric anomalies, classifies technical error logs, correlates related alerts into consolidated incidents, ranks probable root causes with transparent multi-factor evidence, retrieves historical post-mortems and runbooks via RAG, recommends actionable remediations, enforces human-in-the-loop approval, and audits every simulated remediation action.

## Key Capabilities
- **Telemetry Ingestion**: Resilient validation and processing of batch/streaming logs and metric timeseries.
- **Metric Anomaly Detection**: Statistical rolling-window dynamic baselines alongside multivariate Isolation Forest models.
- **Log Classification**: NLP classification pipeline (TF-IDF + Regularized Classifier) categorizing error signatures into domain failure modes with confidence scoring.
- **Alert Correlation & Deduplication**: Multi-heuristic alert grouping (time window, topology dependencies, error taxonomy, trace IDs) delivering high alert reduction.
- **Explainable Root-Cause Ranking**: Multi-factor scoring (temporal sequence 30%, metric anomaly 30%, dependency graph 20%, historical similarity 20%) with transparent evidence chains.
- **Historical Incident RAG**: Semantic retrieval over past incident post-mortems and runbooks with source attribution and strict relevance filtering.
- **Safe Remediation & Audit Logging**: Strict human-in-the-loop approval gate preventing unapproved executions and persisting tamper-evident audit trails.
- **FastAPI REST API**: Comprehensive, production-grade endpoints for telemetry ingestion, incident analysis, root cause inspection, and remediation workflows.
- **Interactive Streamlit Dashboard**: Operations cockpit providing real-time incident triage, topology dependency views, metric charts, RAG evidence inspection, and 1-click approvals.

## Architecture
```
Simulated Services (API Gateway, Order, Payment, Database)
                     │ logs & metrics
                     ▼
             Ingestion & Validation
                     ▼
          PostgreSQL / SQLite Storage
         /           |           \
Anomaly Detection   Log NLP   Alert Grouping
         \           |           /
             Root-Cause Ranking
                     │
            Historical Incident RAG
                     │
             Recommendation Engine
                     │
           [Human Approval Gate]
                     │
        Simulated Remediation & Audit Log
                     │
       FastAPI Backend & Streamlit Dashboard
```

## Repository Structure
```
incident-intelligence-platform/
├── PRD.md
├── PHASES.md
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── data/
│   ├── raw/
│   ├── processed/
│   ├── synthetic/
│   └── knowledge_base/
│       ├── incidents/
│       └── runbooks/
├── notebooks/
├── src/
│   ├── ingestion/
│   ├── anomaly_detection/
│   ├── log_classification/
│   ├── alert_correlation/
│   ├── root_cause/
│   ├── rag/
│   ├── remediation/
│   └── storage/
├── api/
├── dashboard/
├── models/
├── reports/
├── tests/
└── docs/
```

## Quick Start
1. **Activate virtual environment:**
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
2. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```
3. **Run API Server:**
   ```powershell
   uvicorn api.main:app --reload --port 8000
   ```
4. **Launch Dashboard:**
   ```powershell
   streamlit run dashboard/app.py
   ```
