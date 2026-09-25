from app.recovery_action import (
    RecoveryAction,
    RecoveryRiskLevel,
)


RISK_PRIORITY = {
    RecoveryRiskLevel.LOW: 0,
    RecoveryRiskLevel.MEDIUM: 1,
    RecoveryRiskLevel.HIGH: 2,
    RecoveryRiskLevel.CRITICAL: 3,
}


def order_recovery_actions(
    actions: list[RecoveryAction],
) -> list[RecoveryAction]:
    """
    Order candidate recovery actions from lower-risk
    actions to higher-risk actions.

    Actions are never executed here.
    """

    return sorted(
        actions,
        key=lambda action: (
            RISK_PRIORITY.get(
                action.risk_level,
                99,
            ),
            len(action.dependencies),
        ),
    )
