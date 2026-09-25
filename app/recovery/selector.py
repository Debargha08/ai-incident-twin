from app.recovery.ordering import order_recovery_actions
from app.recovery.validator import validate_recovery_actions
from app.recovery.safety_gate import RecoverySafetyGate
from app.recovery_action import RecoveryActionType


class RecoveryActionSelector:
    """
    Select one executable recovery action from AI-generated candidates.

    Selection uses only the investigation target, current environment
    state, structural validation, and the existing safety gate.
    Benchmark ground truth is never used.
    """

    def __init__(self, safety_gate=None) -> None:
        self.safety_gate = safety_gate or RecoverySafetyGate()

    def select(
        self,
        actions,
        root_cause_service: str,
        environment,
    ):
        if not actions:
            return None

        validation_errors = validate_recovery_actions(actions)

        candidates = [
            action
            for index, action in enumerate(actions, start=1)
            if index not in validation_errors
            and action.target_service.strip().lower() == root_cause_service.strip().lower()
        ]

        if not candidates:
            return None

        executable = []

        for action in candidates:
            safety_evaluation = self.safety_gate.evaluate(
                action,
                environment,
            )

            if not safety_evaluation.approved:
                continue

            if not self._can_address_current_state(
                action,
                environment,
            ):
                continue

            executable.append(action)

        if not executable:
            return None

        ordered = order_recovery_actions(executable)

        return ordered[0]

    def _can_address_current_state(
        self,
        action,
        environment,
    ) -> bool:
        target_service = action.target_service.strip()

        if target_service not in environment.services:
            return False

        service = environment.services[target_service]

        if service.status.value == "healthy":
            return True

        return action.action_type in {
            RecoveryActionType.RESTART_SERVICE,
            RecoveryActionType.RESTORE_SERVICE,
        }
