from dataclasses import dataclass, field

from app.intelligence.dependency_graph import DependencyGraph
from app.intelligence.timeline import TimelineEvent
from app.simulation.models import Incident

from app.telemetry.collector import TelemetryBundle


@dataclass
class ServiceEvidence:
    service: str
    anomaly_count: int = 0
    symptoms: list[str] = field(default_factory=list)
    log_levels: list[str] = field(default_factory=list)
    trace_statuses: list[str] = field(default_factory=list)
    trace_durations_ms: list[float] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    dependents: list[str] = field(default_factory=list)


@dataclass
class CorrelatedEvidence:
    incident_id: str
    services: list[ServiceEvidence]
    timeline: list[TimelineEvent]


def correlate_evidence(
    incident: Incident,
    telemetry: TelemetryBundle,
    timeline: list[TimelineEvent],
    dependency_graph: DependencyGraph,
) -> CorrelatedEvidence:
    evidence_by_service = {
        service: ServiceEvidence(service=service)
        for service in incident.affected_services
    }

    for metric in telemetry.metrics:
        if metric.service not in evidence_by_service:
            continue

        evidence = evidence_by_service[metric.service]

        if metric.latency_ms > 100.0:
            evidence.anomaly_count += 1
            evidence.symptoms.append(
                f"Latency: {metric.latency_ms:.1f}ms"
            )

        if metric.error_rate > 0.10:
            evidence.anomaly_count += 1
            evidence.symptoms.append(
                f"Error rate: {metric.error_rate:.2%}"
            )

        if metric.cpu_usage > 80.0:
            evidence.anomaly_count += 1
            evidence.symptoms.append(
                f"CPU usage: {metric.cpu_usage:.1f}%"
            )

        if metric.memory_usage > 80.0:
            evidence.anomaly_count += 1
            evidence.symptoms.append(
                f"Memory usage: {metric.memory_usage:.1f}%"
            )

    for log in telemetry.logs:
        if log.service not in evidence_by_service:
            continue

        evidence_by_service[log.service].log_levels.append(
            log.level.value
        )

    for trace in telemetry.traces:
        if trace.service not in evidence_by_service:
            continue

        evidence = evidence_by_service[trace.service]

        evidence.trace_statuses.append(trace.status)
        evidence.trace_durations_ms.append(
            trace.duration_ms
        )

    for service, evidence in evidence_by_service.items():
        evidence.dependencies = (
            dependency_graph.dependencies_of(service)
        )
        evidence.dependents = (
            dependency_graph.dependents_of(service)
        )

    return CorrelatedEvidence(
        incident_id=incident.incident_id,
        services=list(evidence_by_service.values()),
        timeline=timeline,
    )
