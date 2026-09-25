from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ServiceStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"


class IncidentSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(str, Enum):
    DETECTED = "detected"
    INVESTIGATING = "investigating"
    RECOVERING = "recovering"
    RESOLVED = "resolved"
    FAILED = "failed"


@dataclass
class Service:
    name: str
    version: str = "1.0.0"
    status: ServiceStatus = ServiceStatus.HEALTHY
    latency_ms: float = 50.0
    error_rate: float = 0.0
    request_count: int = 0
    dependencies: list[str] = field(default_factory=list)
    dependency_degraded: bool = False


@dataclass
class TelemetrySnapshot:
    timestamp: datetime
    service: str
    latency_ms: float
    error_rate: float
    cpu_usage: float
    memory_usage: float
    request_rate: float


@dataclass
class Incident:
    incident_id: str
    detected_at: datetime
    severity: IncidentSeverity
    affected_services: list[str]
    symptoms: list[str]
    status: IncidentStatus = IncidentStatus.DETECTED


@dataclass
class FailureScenario:
    name: str
    description: str
    target_service: str
    failure_type: str
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class Anomaly:
    service: str
    timestamp: datetime
    signal: str
    value: float
    threshold: float
    message: str


@dataclass
class FailureEvent:
    timestamp: datetime
    service: str
    failure_type: str
    parameters: dict[str, Any] = field(default_factory=dict)
