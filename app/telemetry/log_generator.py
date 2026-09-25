from datetime import datetime, timezone

from app.simulation.models import Service, ServiceStatus

from .logs import LogEvent, LogLevel, create_log


def generate_service_log(service: Service) -> LogEvent:
    timestamp = datetime.now(timezone.utc)

    if service.status == ServiceStatus.HEALTHY:
        return create_log(
            service=service.name,
            level=LogLevel.INFO,
            message="Service operating normally",
            timestamp=timestamp,
            metadata={
                "status": service.status.value,
                "latency_ms": service.latency_ms,
                "error_rate": service.error_rate,
            },
        )

    if service.status == ServiceStatus.DEGRADED:
        return create_log(
            service=service.name,
            level=LogLevel.WARNING,
            message="Service performance degraded",
            timestamp=timestamp,
            metadata={
                "status": service.status.value,
                "latency_ms": service.latency_ms,
                "error_rate": service.error_rate,
            },
        )

    return create_log(
        service=service.name,
        level=LogLevel.ERROR,
        message="Service failure detected",
        timestamp=timestamp,
        metadata={
            "status": service.status.value,
            "latency_ms": service.latency_ms,
            "error_rate": service.error_rate,
        },
    )


def generate_logs(
    services: dict[str, Service],
) -> list[LogEvent]:
    return [
        generate_service_log(service)
        for service in services.values()
    ]
