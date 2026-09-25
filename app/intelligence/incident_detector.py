from uuid import uuid4

from app.simulation.models import (
    Anomaly,
    Incident,
    IncidentSeverity,
    IncidentStatus,
)


def detect_incident(anomalies: list[Anomaly]) -> Incident | None:
    if not anomalies:
        return None

    affected_services = sorted(
        {anomaly.service for anomaly in anomalies}
    )

    symptoms = [
        anomaly.message
        for anomaly in anomalies
    ]

    severity = _determine_severity(anomalies)

    return Incident(
        incident_id=f"INC-{uuid4().hex[:8]}",
        detected_at=anomalies[0].timestamp,
        severity=severity,
        affected_services=affected_services,
        symptoms=symptoms,
        status=IncidentStatus.DETECTED,
    )


def _determine_severity(
    anomalies: list[Anomaly],
) -> IncidentSeverity:
    if any(
        anomaly.value >= 0.80
        for anomaly in anomalies
    ):
        return IncidentSeverity.CRITICAL

    if any(
        anomaly.value >= 0.50
        for anomaly in anomalies
    ):
        return IncidentSeverity.HIGH

    if any(
        anomaly.value >= 0.25
        for anomaly in anomalies
    ):
        return IncidentSeverity.MEDIUM

    return IncidentSeverity.LOW
