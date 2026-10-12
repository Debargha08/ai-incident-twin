from app.recovery.regression import RecoveryRegressionDetector
from app.simulation.environment import SimulationEnvironment
from app.simulation.models import ServiceStatus


def test_detector_flags_unhealthy_dependent_service():
    environment = SimulationEnvironment()
    environment.services["redis"].status = ServiceStatus.FAILED
    environment.step()

    result = RecoveryRegressionDetector().detect(
        environment,
        ["redis", "user-service", "order-service"],
    )

    assert result.healthy is False
    assert set(result.unhealthy_services) == {
        "redis",
        "user-service",
        "order-service",
    }


def test_detector_accepts_healthy_services():
    environment = SimulationEnvironment()

    result = RecoveryRegressionDetector().detect(
        environment,
        ["redis", "user-service", "order-service"],
    )

    assert result.healthy is True
    assert result.unhealthy_services == []


def test_detector_flags_excessive_latency_even_when_status_is_healthy():
    environment = SimulationEnvironment()
    environment.services["order-service"].latency_ms = 150.0

    result = RecoveryRegressionDetector().detect(
        environment,
        ["order-service"],
    )

    assert result.healthy is False
    assert result.unhealthy_services == ["order-service"]


def test_detector_flags_unknown_affected_service():
    environment = SimulationEnvironment()

    result = RecoveryRegressionDetector().detect(
        environment,
        ["missing-service"],
    )

    assert result.healthy is False
    assert result.unhealthy_services == ["missing-service"]
