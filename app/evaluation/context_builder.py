from datetime import datetime, timezone

from app.evaluation.runner import BenchmarkRunner
from app.intelligence.anomaly_detector import detect_anomalies
from app.intelligence.dependency_graph import DependencyGraph
from app.intelligence.incident_context import (
    IncidentContext,
    build_incident_context,
)
from app.intelligence.incident_detector import detect_incident
from app.intelligence.timeline import build_failure_timeline
from app.intelligence.evidence import correlate_evidence
from app.telemetry.collector import collect_telemetry
from app.telemetry.log_generator import generate_logs
from app.telemetry.trace_generator import generate_request_trace


class BenchmarkContextBuilder:
    def __init__(self, runner: BenchmarkRunner):
        self.runner = runner

    def build(self, scenario):
        result = self.runner.run(scenario)

        snapshots = list(
            self.runner.environment.telemetry_history
        )

        anomalies = []

        for snapshot in snapshots:
            anomalies.extend(
                detect_anomalies(snapshot)
            )

        incident = detect_incident(anomalies)

        if incident is None:
            raise RuntimeError(
                f"No incident detected for {scenario.name}"
            )

        timeline = build_failure_timeline(anomalies)

        logs = generate_logs(
            self.runner.environment.services
        )

        traces = generate_request_trace(
            self.runner.environment
        )

        telemetry = collect_telemetry(
            metrics=snapshots,
            logs=logs,
            traces=traces,
            collected_at=datetime.now(timezone.utc),
        )

        dependency_graph = DependencyGraph(
            self.runner.environment.services
        )

        evidence = correlate_evidence(
            incident=incident,
            telemetry=telemetry,
            timeline=timeline,
            dependency_graph=dependency_graph,
        )

        context = build_incident_context(
            incident=incident,
            timeline=timeline,
            evidence=evidence,
        )

        return result, context
