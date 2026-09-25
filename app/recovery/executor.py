from dataclasses import dataclass

from app.recovery_action import RecoveryActionType
from app.recovery.execution_log import RecoveryExecutionLog
from app.recovery.safety import SafetyEvaluation
from app.simulation.services import reset_service


@dataclass
class RecoveryExecutionResult:
    success: bool
    action_type: str
    target_service: str
    message: str


class RecoveryExecutor:
    """
    Execute recovery actions that have already passed
    the Phase 8 safety gate.

    This component does not perform safety evaluation.
    """

    def execute(
        self,
        action,
        safety_evaluation: SafetyEvaluation,
        environment,
    ) -> RecoveryExecutionResult:

        if not safety_evaluation.approved:
            result = RecoveryExecutionResult(
                success=False,
                action_type=action.action_type.value,
                target_service=action.target_service,
                message=(
                    "Recovery action was not executed "
                    "because the safety gate blocked it."
                ),
            )

            environment.recovery_execution_history.append(
                RecoveryExecutionLog.from_result(result)
            )

            return result

        if action.action_type == RecoveryActionType.RESTART_SERVICE:
            result = self._restart_service(
                action,
                environment,
            )

        elif action.action_type == RecoveryActionType.RESTORE_SERVICE:
            result = self._restore_service(
                action,
                environment,
            )

        elif action.action_type == RecoveryActionType.ROLLBACK_VERSION:
            result = self._rollback_version(
                action,
                environment,
            )

        elif action.action_type == RecoveryActionType.CLEAR_CACHE:
            result = self._clear_cache(
                action,
                environment,
            )

        elif action.action_type == RecoveryActionType.REDIRECT_TRAFFIC:
            result = self._redirect_traffic(
                action,
                environment,
            )

        else:
            result = RecoveryExecutionResult(
                success=False,
                action_type=action.action_type.value,
                target_service=action.target_service,
                message=(
                    "Recovery action execution is not "
                    "implemented yet."
                ),
            )

        environment.recovery_execution_history.append(
            RecoveryExecutionLog.from_result(result)
        )

        return result

    def _restart_service(
        self,
        action,
        environment,
    ) -> RecoveryExecutionResult:

        target_service = action.target_service.strip()

        if target_service not in environment.services:
            return RecoveryExecutionResult(
                success=False,
                action_type=action.action_type.value,
                target_service=target_service,
                message="Cannot restart unknown service.",
            )

        service = environment.services[target_service]

        reset_service(service)

        return RecoveryExecutionResult(
            success=True,
            action_type=action.action_type.value,
            target_service=target_service,
            message=(
                f"Service '{target_service}' "
                "was restarted successfully."
            ),
        )

    def _restore_service(
        self,
        action,
        environment,
    ) -> RecoveryExecutionResult:

        target_service = action.target_service.strip()

        if target_service not in environment.services:
            return RecoveryExecutionResult(
                success=False,
                action_type=action.action_type.value,
                target_service=target_service,
                message="Cannot restore unknown service.",
            )

        service = environment.services[target_service]

        reset_service(service)

        return RecoveryExecutionResult(
            success=True,
            action_type=action.action_type.value,
            target_service=target_service,
            message=(
                f"Service '{target_service}' "
                "was restored successfully."
            ),
        )

    def _redirect_traffic(
        self,
        action,
        environment,
    ) -> RecoveryExecutionResult:

        target_service = action.target_service.strip()

        if target_service not in environment.services:
            return RecoveryExecutionResult(
                success=False,
                action_type=action.action_type.value,
                target_service=target_service,
                message="Cannot redirect traffic from unknown service.",
            )

        if target_service not in environment.traffic_routes:
            return RecoveryExecutionResult(
                success=False,
                action_type=action.action_type.value,
                target_service=target_service,
                message="Traffic route does not exist for target service.",
            )

        backup_service = action.parameters.get("redirect_to")

        if not backup_service:
            return RecoveryExecutionResult(
                success=False,
                action_type=action.action_type.value,
                target_service=target_service,
                message="Traffic redirection target was not provided.",
            )

        backup_service = backup_service.strip()

        if backup_service not in environment.services:
            return RecoveryExecutionResult(
                success=False,
                action_type=action.action_type.value,
                target_service=target_service,
                message=(
                    f"Cannot redirect traffic to unknown service "
                    f"'{backup_service}'."
                ),
            )

        environment.traffic_routes[target_service] = backup_service

        return RecoveryExecutionResult(
            success=True,
            action_type=action.action_type.value,
            target_service=target_service,
            message=(
                f"Traffic for '{target_service}' was redirected "
                f"to '{backup_service}' successfully."
            ),
        )

    def _clear_cache(
        self,
        action,
        environment,
    ) -> RecoveryExecutionResult:

        target_service = action.target_service.strip()

        if target_service != "redis":
            return RecoveryExecutionResult(
                success=False,
                action_type=action.action_type.value,
                target_service=target_service,
                message=(
                    "Cache clearing is only supported "
                    "for Redis."
                ),
            )

        if target_service not in environment.services:
            return RecoveryExecutionResult(
                success=False,
                action_type=action.action_type.value,
                target_service=target_service,
                message="Cannot clear cache for unknown service.",
            )

        environment.cache_state[target_service] = False

        return RecoveryExecutionResult(
            success=True,
            action_type=action.action_type.value,
            target_service=target_service,
            message=(
                "Redis cache was cleared successfully."
            ),
        )

    def _rollback_version(
        self,
        action,
        environment,
    ) -> RecoveryExecutionResult:

        target_service = action.target_service.strip()

        if target_service not in environment.services:
            return RecoveryExecutionResult(
                success=False,
                action_type=action.action_type.value,
                target_service=target_service,
                message="Cannot rollback unknown service.",
            )

        service = environment.services[target_service]

        current_version = service.version

        if not current_version:
            return RecoveryExecutionResult(
                success=False,
                action_type=action.action_type.value,
                target_service=target_service,
                message="Service has no version information.",
            )

        if "." not in current_version:
            return RecoveryExecutionResult(
                success=False,
                action_type=action.action_type.value,
                target_service=target_service,
                message="Service version format is invalid.",
            )

        parts = current_version.split(".")

        if len(parts) != 3:
            return RecoveryExecutionResult(
                success=False,
                action_type=action.action_type.value,
                target_service=target_service,
                message="Service version format is invalid.",
            )

        try:
            major = int(parts[0])
            minor = int(parts[1])
            patch = int(parts[2])
        except ValueError:
            return RecoveryExecutionResult(
                success=False,
                action_type=action.action_type.value,
                target_service=target_service,
                message="Service version format is invalid.",
            )

        if patch > 0:
            previous_version = (
                f"{major}.{minor}.{patch - 1}"
            )

        elif minor > 0:
            previous_version = (
                f"{major}.{minor - 1}.0"
            )

        elif major > 0:
            previous_version = (
                f"{major - 1}.0.0"
            )

        else:
            return RecoveryExecutionResult(
                success=False,
                action_type=action.action_type.value,
                target_service=target_service,
                message=(
                    "No previous version is available."
                ),
            )

        service.version = previous_version

        return RecoveryExecutionResult(
            success=True,
            action_type=action.action_type.value,
            target_service=target_service,
            message=(
                f"Service '{target_service}' "
                f"rolled back from {current_version} "
                f"to {previous_version}."
            ),
        )
