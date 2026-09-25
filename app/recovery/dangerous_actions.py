from app.recovery_action import (
    RecoveryAction,
    RecoveryActionType,
    RecoveryRiskLevel,
)


def check_dangerous_action(
    action: RecoveryAction,
) -> list[str]:
    """
    Apply explicit safety policies to recovery actions.

    Returns a list of policy violations.
    """

    failures: list[str] = []

    # Critical-risk actions require manual approval.
    if action.risk_level == RecoveryRiskLevel.CRITICAL:
        failures.append(
            "Critical-risk actions require manual approval"
        )

    # Traffic redirection can affect production-wide
    # request routing and is not autonomously approved.
    if action.action_type == RecoveryActionType.REDIRECT_TRAFFIC:
        failures.append(
            "Traffic redirection requires manual approval"
        )

    # Rollbacks can change deployed application versions.
    if action.action_type == RecoveryActionType.ROLLBACK_VERSION:
        if action.risk_level in {
            RecoveryRiskLevel.HIGH,
            RecoveryRiskLevel.CRITICAL,
        }:
            failures.append(
                "High-risk or critical rollback requires manual approval"
            )

    return failures
