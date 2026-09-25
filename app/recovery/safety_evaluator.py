from app.recovery_action import (
    RecoveryAction,
    RecoveryActionType,
    RecoveryRiskLevel,
)
from app.recovery.safety import (
    SafetyDecision,
    SafetyEvaluation,
)


class RecoverySafetyEvaluator:
    """
    Evaluate whether a recovery action is safe to execute.

    This component performs safety checks only.
    It never executes recovery actions.
    """

    def evaluate(
        self,
        action: RecoveryAction,
        environment,
    ) -> SafetyEvaluation:

        checks_passed: list[str] = []
        checks_failed: list[str] = []

        # -------------------------------------------------
        # 1. Target service validation
        # -------------------------------------------------

        target_service = action.target_service.strip()

        if target_service in environment.services:
            checks_passed.append(
                "Target service exists"
            )
        else:
            checks_failed.append(
                "Target service does not exist"
            )

        # -------------------------------------------------
        # 2. Target format validation
        # -------------------------------------------------

        if "," in target_service:
            checks_failed.append(
                "Target service must identify exactly one service"
            )
        else:
            checks_passed.append(
                "Target service is uniquely specified"
            )

        # -------------------------------------------------
        # 3. Preconditions validation
        # -------------------------------------------------

        if action.preconditions:
            checks_passed.append(
                "Recovery preconditions are defined"
            )
        else:
            checks_failed.append(
                "Recovery action has no preconditions"
            )

        # -------------------------------------------------
        # 4. Expected outcome validation
        # -------------------------------------------------

        if action.expected_outcomes:
            checks_passed.append(
                "Expected recovery outcomes are defined"
            )
        else:
            checks_failed.append(
                "Recovery action has no expected outcomes"
            )

        # -------------------------------------------------
        # 5. Dependency validation
        # -------------------------------------------------

        invalid_dependencies = [
            dependency
            for dependency in action.dependencies
            if dependency not in environment.services
        ]

        if invalid_dependencies:
            checks_failed.append(
                "Recovery action contains invalid dependencies"
            )
        else:
            checks_passed.append(
                "Recovery dependencies are valid"
            )

        # -------------------------------------------------
        # 6. Risk validation
        # -------------------------------------------------

        if action.risk_level == RecoveryRiskLevel.CRITICAL:
            checks_failed.append(
                "Critical-risk recovery actions are blocked"
            )
        else:
            checks_passed.append(
                "Recovery risk level is within allowed limits"
            )

        # -------------------------------------------------
        # 7. Recovery action validation
        # -------------------------------------------------

        allowed_actions = {
            RecoveryActionType.RESTART_SERVICE,
            RecoveryActionType.RESTORE_SERVICE,
            RecoveryActionType.ROLLBACK_VERSION,
            RecoveryActionType.REDIRECT_TRAFFIC,
            RecoveryActionType.CLEAR_CACHE,
        }

        if action.action_type in allowed_actions:
            checks_passed.append(
                "Recovery action type is allowed"
            )
        else:
            checks_failed.append(
                "Recovery action type is not allowed"
            )

        # -------------------------------------------------
        # Final decision
        # -------------------------------------------------

        if checks_failed:
            return SafetyEvaluation(
                decision=SafetyDecision.BLOCKED,
                risk_level=action.risk_level,
                checks_passed=checks_passed,
                checks_failed=checks_failed,
                reason=(
                    "Recovery action failed one or more "
                    "safety checks."
                ),
            )

        return SafetyEvaluation(
            decision=SafetyDecision.APPROVED,
            risk_level=action.risk_level,
            checks_passed=checks_passed,
            checks_failed=[],
            reason=(
                "Recovery action passed all safety checks."
            ),
        )
