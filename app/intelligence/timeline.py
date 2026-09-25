from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from app.simulation.models import Anomaly


class TimelineEventType(str, Enum):
    ANOMALY = "anomaly"
    LOG = "log"
    TRACE = "trace"


@dataclass
class TimelineEvent:
    timestamp: datetime
    event_type: TimelineEventType
    service: str
    description: str


def build_failure_timeline(
    anomalies: list[Anomaly],
) -> list[TimelineEvent]:
    events = [
        TimelineEvent(
            timestamp=anomaly.timestamp,
            event_type=TimelineEventType.ANOMALY,
            service=anomaly.service,
            description=anomaly.message,
        )
        for anomaly in anomalies
    ]

    return sorted(
        events,
        key=lambda event: event.timestamp,
    )
