from .models import Service, ServiceStatus


def create_default_services() -> dict[str, Service]:
    return {
        "user-service": Service(
            name="user-service",
            version="1.0.0",
            dependencies=["redis"],
        ),
        "order-service": Service(
            name="order-service",
            version="1.0.0",
            dependencies=["payment-service", "redis"],
        ),
        "payment-service": Service(
            name="payment-service",
            version="1.0.0",
            dependencies=["postgresql"],
        ),
        "redis": Service(
            name="redis",
            version="7.2",
        ),
        "postgresql": Service(
            name="postgresql",
            version="16",
        ),
    }


def reset_service(service: Service) -> None:
    service.status = ServiceStatus.HEALTHY
    service.latency_ms = 50.0
    service.error_rate = 0.0
    service.dependency_degraded = False
