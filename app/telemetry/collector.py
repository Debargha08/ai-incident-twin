from dataclasses import dataclass
from datetime import datetime

from app.simulation.models import TelemetrySnapshot

from .logs import LogEvent
from .traces import TraceSpan


@dataclass
class TelemetryBundle:
    collected_at: datetime
    metrics: list[TelemetrySnapshot]
    logs: list[LogEvent]
    traces: list[TraceSpan]


def collect_telemetry(
    metrics: list[TelemetrySnapshot],
    logs: list[LogEvent],
    traces: list[TraceSpan],
    collected_at: datetime,
) -> TelemetryBundle:
    return TelemetryBundle(
        collected_at=collected_at,
        metrics=metrics,
        logs=logs,
        traces=traces,
    )
