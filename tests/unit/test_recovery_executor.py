from types import SimpleNamespace

from app.recovery.executor import RecoveryExecutor
from app.recovery.safety import SafetyEvaluation
from app.recovery_action import RecoveryAction, RecoveryActionType
from app.simulation.environment import SimulationEnvironment
from app.simulation.models import ServiceStatus


def make_action(target="redis"):
    return RecoveryAction(
        action_type=RecoveryActionType.RESTART_SERVICE,
        target_service=target,
        reason="Test recovery",
    )


def test_restart_recovers_failed_service():
    environment = SimulationEnvironment()
    environment.services["redis"].status = ServiceStatus.FAILED
    environment.services["redis"].error_rate = 1.0

    safety = SimpleNamespace(approved=True)
    result = RecoveryExecutor().execute(
        action=make_action(),
        safety_evaluation=safety,
        environment=environment,
    )

    assert result.success is True
    assert environment.services["redis"].status == ServiceStatus.HEALTHY
    assert environment.services["redis"].error_rate == 0.0


def test_unsafe_action_is_not_executed():
    environment = SimulationEnvironment()
    environment.services["redis"].status = ServiceStatus.FAILED

    safety = SimpleNamespace(approved=False)
    result = RecoveryExecutor().execute(
        action=make_action(),
        safety_evaluation=safety,
        environment=environment,
    )

    assert result.success is False
    assert environment.services["redis"].status == ServiceStatus.FAILED
    assert len(environment.recovery_execution_history) == 1


def test_restart_of_unknown_service_fails():
    environment = SimulationEnvironment()

    safety = SimpleNamespace(approved=True)
    result = RecoveryExecutor().execute(
        action=make_action("missing-service"),
        safety_evaluation=safety,
        environment=environment,
    )

    assert result.success is False
    assert "unknown service" in result.message.lower()
