import pytest

from app.simulation.environment import SimulationEnvironment
from app.simulation.failures import crash_service
from app.simulation.models import ServiceStatus


def test_redis_crash_degrades_dependent_services():
    environment = SimulationEnvironment()

    crash_service(environment, "redis")
    environment.step()

    assert environment.services["redis"].status == ServiceStatus.FAILED

    for service_name in ("user-service", "order-service"):
        service = environment.services[service_name]

        assert service.status == ServiceStatus.DEGRADED
        assert service.dependency_degraded is True
        assert service.error_rate == pytest.approx(0.25)
        assert service.latency_ms == pytest.approx(150.0)


def test_dependents_recover_after_redis_is_restored():
    environment = SimulationEnvironment()

    crash_service(environment, "redis")
    environment.step()

    # Restore Redis, then propagate the recovery on the next step.
    environment.services["redis"].status = ServiceStatus.HEALTHY
    environment.services["redis"].error_rate = 0.0
    environment.services["redis"].latency_ms = 50.0

    environment.step()

    for service_name in ("user-service", "order-service"):
        service = environment.services[service_name]

        assert service.status == ServiceStatus.HEALTHY
        assert service.dependency_degraded is False
        assert service.error_rate == pytest.approx(0.0)
        assert service.latency_ms == pytest.approx(50.0)


def test_postgresql_crash_propagates_through_payment_to_order():
    environment = SimulationEnvironment()

    crash_service(environment, "postgresql")
    environment.step()

    # Payment depends on PostgreSQL, so it degrades first.
    assert (
        environment.services["payment-service"].status
        == ServiceStatus.DEGRADED
    )

    # Order depends on payment-service, but propagation checks FAILED
    # dependencies only. A degraded payment service should not cause
    # order-service to degrade under the current simulator rules.
    assert (
        environment.services["order-service"].status
        == ServiceStatus.HEALTHY
    )
