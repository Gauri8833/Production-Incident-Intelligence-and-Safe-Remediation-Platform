import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory is project root
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables
load_dotenv(BASE_DIR / ".env")

# Directory paths
DATA_DIR = BASE_DIR / os.getenv("DATA_DIR", "data")
SYNTHETIC_DATA_DIR = DATA_DIR / "synthetic"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
KNOWLEDGE_BASE_DIR = DATA_DIR / "knowledge_base"
INCIDENTS_KB_DIR = KNOWLEDGE_BASE_DIR / "incidents"
RUNBOOKS_KB_DIR = KNOWLEDGE_BASE_DIR / "runbooks"
MODEL_DIR = BASE_DIR / os.getenv("MODEL_DIR", "models")
REPORTS_DIR = BASE_DIR / "reports"
DOCS_DIR = BASE_DIR / "docs"

# Ensure runtime directories exist
for path in [
    SYNTHETIC_DATA_DIR,
    PROCESSED_DATA_DIR,
    INCIDENTS_KB_DIR,
    RUNBOOKS_KB_DIR,
    MODEL_DIR,
    REPORTS_DIR,
    DOCS_DIR,
]:
    path.mkdir(parents=True, exist_ok=True)

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/incident_db.sqlite3")

# Vector Index
VECTOR_INDEX_PATH = BASE_DIR / os.getenv("VECTOR_INDEX_PATH", "data/processed/vector_index")

# Core Domain Constants
SERVICES = ["api_gateway", "order_service", "payment_service", "database"]

METRIC_NAMES = [
    "api_latency_ms",
    "error_rate_percent",
    "request_count",
    "cpu_percent",
    "memory_percent",
    "database_connections_percent",
]

FAILURE_SCENARIOS = [
    "normal",
    "database_failure",
    "payment_failure",
    "network_failure",
    "authentication_failure",
    "deployment_failure",
    "memory_failure",
    "unknown",
]

LOG_LEVELS = ["INFO", "WARN", "WARNING", "ERROR", "CRITICAL"]

SERVICE_DEPENDENCIES = {
    "api_gateway": ["order_service"],
    "order_service": ["payment_service", "database"],
    "payment_service": ["database"],
    "database": [],
}
