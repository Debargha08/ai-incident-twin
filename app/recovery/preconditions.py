from app.recovery_action import RecoveryActionType


def check_preconditions(action, environment) -> list[str]:
    """
    Check whether the current simulation environment
    satisfies the recovery action preconditions.

    Returns a list of failed preconditions.
    """

    failures: list[str] = []

    target_service = action.target_service.strip()

    if target_service not in environment.services:
        failures.append(
            "Target service does not exist"
        )
        return failures

    service = environment.services[target_service]

    if action.action_type == RecoveryActionType.RESTART_SERVICE:
        if service.status.value == "healthy":
            failures.append(
                "Target service is already healthy"
            )

    elif action.action_type == RecoveryActionType.RESTORE_SERVICE:
        if service.status.value == "healthy":
            failures.append(
                "Target service is already healthy"
            )

    elif action.action_type == RecoveryActionType.ROLLBACK_VERSION:
        if not service.version:
            failures.append(
                "Target service has no version information"
            )

    elif action.action_type == RecoveryActionType.CLEAR_CACHE:
        if target_service != "redis":
            failures.append(
                "Cache clearing is only supported for Redis"
            )

    elif action.action_type == RecoveryActionType.REDIRECT_TRAFFIC:
        if service.status.value == "healthy":
            failures.append(
                "Traffic redirection is unnecessary for a healthy service"
            )

    return failures
