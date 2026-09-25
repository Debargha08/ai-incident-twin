from .models import ServiceStatus


def crash_service(environment, service_name: str) -> None:
    service = environment.services[service_name]

    service.status = ServiceStatus.FAILED
    service.error_rate = 1.0

    environment.record_failure(
        service_name=service_name,
        failure_type="service_crash",
    )


def degrade_service(environment, service_name: str) -> None:
    service = environment.services[service_name]

    service.status = ServiceStatus.DEGRADED
    service.error_rate = 0.20

    environment.record_failure(
        service_name=service_name,
        failure_type="service_degradation",
    )


def inject_latency(
    environment,
    service_name: str,
    multiplier: float = 5.0,
) -> None:
    service = environment.services[service_name]

    service.status = ServiceStatus.DEGRADED
    service.latency_ms *= multiplier

    environment.record_failure(
        service_name=service_name,
        failure_type="latency_increase",
        parameters={"multiplier": multiplier},
    )


def restore_service(environment, service_name: str) -> None:
    service = environment.services[service_name]

    service.status = ServiceStatus.HEALTHY
    service.latency_ms = 50.0
    service.error_rate = 0.0
