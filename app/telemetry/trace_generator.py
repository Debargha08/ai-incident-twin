from datetime import datetime, timezone
from uuid import uuid4

from app.simulation.models import ServiceStatus

from .traces import TraceSpan, create_span


def generate_request_trace(environment) -> list[TraceSpan]:
    trace_id = f"trace-{uuid4().hex[:8]}"
    timestamp = datetime.now(timezone.utc)

    spans: list[TraceSpan] = []

    user_service = environment.services["user-service"]
    order_service = environment.services["order-service"]
    redis = environment.services["redis"]
    payment_service = environment.services["payment-service"]
    postgresql = environment.services["postgresql"]

    user_span = create_span(
        service="user-service",
        operation="handle_request",
        start_time=timestamp,
        duration_ms=20.0 if user_service.status == ServiceStatus.HEALTHY else 30.0,
        status="ok" if user_service.status == ServiceStatus.HEALTHY else "error",
        trace_id=trace_id,
    )

    spans.append(user_span)

    order_span = create_span(
        service="order-service",
        operation="create_order",
        start_time=timestamp,
        duration_ms=15.0 if order_service.status == ServiceStatus.HEALTHY else 80.0,
        status="ok" if order_service.status == ServiceStatus.HEALTHY else "error",
        parent_span_id=user_span.span_id,
        trace_id=trace_id,
    )

    spans.append(order_span)

    redis_failed = redis.status == ServiceStatus.FAILED

    redis_span = create_span(
        service="redis",
        operation="cache_lookup",
        start_time=timestamp,
        duration_ms=400.0 if redis_failed else 5.0,
        status="error" if redis_failed else "ok",
        parent_span_id=order_span.span_id,
        metadata={
            "dependency": "order-service",
        },
        trace_id=trace_id,
    )

    spans.append(redis_span)

    payment_span = create_span(
        service="payment-service",
        operation="process_payment",
        start_time=timestamp,
        duration_ms=10.0 if payment_service.status == ServiceStatus.HEALTHY else 50.0,
        status="ok" if payment_service.status == ServiceStatus.HEALTHY else "error",
        parent_span_id=order_span.span_id,
        trace_id=trace_id,
    )

    spans.append(payment_span)

    database_span = create_span(
        service="postgresql",
        operation="database_query",
        start_time=timestamp,
        duration_ms=5.0 if postgresql.status == ServiceStatus.HEALTHY else 100.0,
        status="ok" if postgresql.status == ServiceStatus.HEALTHY else "error",
        parent_span_id=payment_span.span_id,
        trace_id=trace_id,
    )

    spans.append(database_span)

    return spans
