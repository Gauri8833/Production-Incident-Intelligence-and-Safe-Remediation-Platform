from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class IncidentStatus(str, Enum):
    NEW = "NEW"
    INVESTIGATING = "INVESTIGATING"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    MITIGATED = "MITIGATED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class SeverityLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RemediationDecision(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class LogRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    timestamp: datetime
    service_name: str
    level: str
    message: str
    trace_id: Optional[str] = None
    host: Optional[str] = "host-app-01"
    environment: Optional[str] = "production"
    scenario: Optional[str] = None


class MetricRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    timestamp: datetime
    service_name: str
    metric_name: str
    metric_value: float
    scenario: Optional[str] = None


class AnomalyResult(BaseModel):
    timestamp: datetime
    service_name: str
    metric_name: str
    metric_value: float
    anomaly_score: float
    is_anomaly: bool
    severity: SeverityLevel
    model_version: str


class LogClassificationResult(BaseModel):
    log_id: Optional[str] = None
    service_name: Optional[str] = None
    message: str
    predicted_label: str
    confidence: float
    model_version: str
    is_review_required: bool = False


class Alert(BaseModel):
    id: str
    timestamp: datetime
    service_name: str
    alert_type: str
    severity: SeverityLevel
    description: str
    status: str = "OPEN"
    trace_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Incident(BaseModel):
    incident_id: str
    created_at: datetime
    updated_at: datetime
    severity: SeverityLevel
    status: IncidentStatus
    affected_services: List[str]
    summary: str
    related_alerts: List[str]
    start_time: datetime
    end_time: Optional[datetime] = None
    raw_alert_count: int = 0
    grouped_incident_count: int = 1
    reduction_percentage: float = 0.0
    correlation_reason: Optional[str] = None


class RootCausePrediction(BaseModel):
    candidate_cause: str
    confidence: float
    evidence: List[str]
    alternatives: List[str]
    model_version: str = "scoring-v1"


class RAGMatch(BaseModel):
    source_id: str
    title: str
    similarity_score: float
    excerpt: str
    resolved_by: Optional[str] = None


class Recommendation(BaseModel):
    id: str
    incident_id: str
    action: str
    description: str
    reason: str
    evidence: List[str]
    confidence: float
    risk_level: SeverityLevel
    requires_approval: bool = True
    status: str = "PENDING"  # PENDING, APPROVED, REJECTED, EXECUTED_SIMULATION, FAILED_SIMULATION


class ApprovalRequest(BaseModel):
    approver: str
    decision: RemediationDecision
    comment: Optional[str] = ""


class ApprovalRecord(BaseModel):
    id: str
    recommendation_id: str
    approver: str
    decision: RemediationDecision
    comment: Optional[str] = ""
    decided_at: datetime


class AuditLogEntry(BaseModel):
    id: str
    actor: str
    action: str
    resource: str
    resource_id: str
    decision: Optional[str] = None
    comment: Optional[str] = None
    timestamp: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)
