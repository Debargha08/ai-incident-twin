from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4


@dataclass
class TraceSpan:
    trace_id: str
    span_id: str
    service: str
    operation: str
    start_time: datetime
    duration_ms: float
    status: str
    parent_span_id: str | None = None
    metadata: dict = field(default_factory=dict)


def create_span(
    service: str,
    operation: str,
    start_time: datetime,
    duration_ms: float,
    status: str,
    parent_span_id: str | None = None,
    metadata: dict | None = None,
    trace_id: str | None = None,
) -> TraceSpan:
    return TraceSpan(
        trace_id=trace_id or f"trace-{uuid4().hex[:8]}",
        span_id=f"span-{uuid4().hex[:8]}",
        service=service,
        operation=operation,
        start_time=start_time,
        duration_ms=duration_ms,
        status=status,
        parent_span_id=parent_span_id,
        metadata=metadata or {},
    )
