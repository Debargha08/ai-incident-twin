from app.recovery.executor import RecoveryExecutor
from app.recovery.safety import SafetyDecision, SafetyEvaluation
from app.recovery.safety_gate import RecoverySafetyGate
from app.recovery.verifier import RecoveryVerifier
from app.recovery_action import (
    RecoveryAction,
    RecoveryActionType,
    RecoveryRiskLevel,
)
from app.simulation.environment import SimulationEnvironment
from app.simulation.failures import crash_service
from app.simulation.models import ServiceStatus


def make_restart_action(service_name):
    return RecoveryAction(
        action_type=RecoveryActionType.RESTART_SERVICE,
        target_service=service_name,
        reason="Restore service health after a simulated crash",
        preconditions=["The target service exists"],
        expected_outcomes=["The service returns to healthy status"],
        risk_level=RecoveryRiskLevel.LOW,
    )


def test_approved_redis_restart_restores_service_and_dependents():
    environment = SimulationEnvironment()
    gate = RecoverySafetyGate()
    executor = RecoveryExecutor()
    verifier = RecoveryVerifier()

    crash_service(environment, "redis")
    environment.step()

    assert environment.services["user-service"].status == ServiceStatus.DEGRADED
    assert environment.services["order-service"].status == ServiceStatus.DEGRADED

    action = make_restart_action("redis")
    evaluation = gate.evaluate(action, environment)

    assert evaluation.approved, evaluation.checks_failed

    result = executor.execute(action, evaluation, environment)

    assert result.success, result.message
    assert verifier.verify(environment, "redis").healthy

    # The simulator propagates dependency recovery on the next step.
    environment.step()

    assert verifier.verify(environment, "user-service").healthy
    assert verifier.verify(environment, "order-service").healthy


def test_blocked_action_does_not_change_failed_service():
    environment = SimulationEnvironment()
    executor = RecoveryExecutor()

    crash_service(environment, "redis")
    action = make_restart_action("redis")

    blocked = SafetyEvaluation(
        decision=SafetyDecision.BLOCKED,
        risk_level=action.risk_level,
        checks_passed=[],
        checks_failed=["Blocked by stress-test policy"],
        reason="Stress test: action must not execute",
    )

    result = executor.execute(action, blocked, environment)

    assert result.success is False
    assert environment.services["redis"].status == ServiceStatus.FAILED
    assert len(environment.recovery_execution_history) == 1


def test_unknown_service_restart_fails_and_verification_rejects_target():
    environment = SimulationEnvironment()
    gate = RecoverySafetyGate()
    executor = RecoveryExecutor()
    verifier = RecoveryVerifier()

    action = make_restart_action("missing-service")

    # Even if a caller mistakenly supplies an approved evaluation,
    # the executor must reject an unknown target.
    approved = SafetyEvaluation(
        decision=SafetyDecision.APPROVED,
        risk_level=action.risk_level,
        checks_passed=["Test-provided approval"],
        checks_failed=[],
        reason="Executor boundary test",
    )

    result = executor.execute(action, approved, environment)

    assert result.success is False
    assert "unknown service" in result.message.lower()
    assert verifier.verify(environment, "missing-service").healthy is False
