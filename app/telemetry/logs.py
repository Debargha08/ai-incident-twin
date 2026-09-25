from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class LogLevel(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass
class LogEvent:
    timestamp: datetime
    service: str
    level: LogLevel
    message: str
    metadata: dict


def create_log(
    service: str,
    level: LogLevel,
    message: str,
    timestamp: datetime,
    metadata: dict | None = None,
) -> LogEvent:
    return LogEvent(
        timestamp=timestamp,
        service=service,
        level=level,
        message=message,
        metadata=metadata or {},
    )
