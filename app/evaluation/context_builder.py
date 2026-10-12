from datetime import datetime, timezone

from app.evaluation.runner import BenchmarkRunner
from app.intelligence.anomaly_detector import detect_anomalies
from app.intelligence.dependency_graph import DependencyGraph
from app.intelligence.incident_context import (
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
        return result, self.build_current_context(scenario.name)

    def build_current_context(self, scenario_name: str):
        environment = self.runner.environment

        snapshots = list(environment.telemetry_history)
        anomalies = []

        for snapshot in snapshots:
            anomalies.extend(detect_anomalies(snapshot))

        incident = detect_incident(anomalies)

        if incident is None:
            raise RuntimeError(
                f"No incident detected for {scenario_name}"
            )

        timeline = build_failure_timeline(anomalies)

        logs = generate_logs(environment.services)
        traces = generate_request_trace(environment)

        telemetry = collect_telemetry(
            metrics=snapshots,
            logs=logs,
            traces=traces,
            collected_at=datetime.now(timezone.utc),
        )

        dependency_graph = DependencyGraph(environment.services)

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

        return context
