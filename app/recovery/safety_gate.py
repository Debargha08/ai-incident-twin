from app.recovery.dangerous_actions import (
    check_dangerous_action,
)
from app.recovery.dependency_safety import (
    check_dependency_safety,
)
from app.recovery.preconditions import (
    check_preconditions,
)
from app.recovery.safety import (
    SafetyDecision,
    SafetyEvaluation,
)
from app.recovery.safety_evaluator import (
    RecoverySafetyEvaluator,
)


class RecoverySafetyGate:
    """
    Final safety boundary before recovery execution.

    The gate evaluates an action using all Phase 8
    safety checks. It never executes the action.
    """

    def __init__(self) -> None:
        self.evaluator = RecoverySafetyEvaluator()

    def evaluate(
        self,
        action,
        environment,
    ) -> SafetyEvaluation:

        base_evaluation = self.evaluator.evaluate(
            action,
            environment,
        )

        checks_passed = list(
            base_evaluation.checks_passed
        )
        checks_failed = list(
            base_evaluation.checks_failed
        )

        # -------------------------------------------------
        # Preconditions
        # -------------------------------------------------

        precondition_failures = check_preconditions(
            action,
            environment,
        )

        if precondition_failures:
            checks_failed.extend(
                precondition_failures
            )
        else:
            checks_passed.append(
                "Recovery preconditions are satisfied"
            )

        # -------------------------------------------------
        # Dependency safety
        # -------------------------------------------------

        dependency_failures = check_dependency_safety(
            action,
            environment,
        )

        if dependency_failures:
            checks_failed.extend(
                dependency_failures
            )
        else:
            checks_passed.append(
                "Recovery dependency relationships are safe"
            )

        # -------------------------------------------------
        # Dangerous-action policy
        # -------------------------------------------------

        dangerous_action_failures = (
            check_dangerous_action(action)
        )

        if dangerous_action_failures:
            checks_failed.extend(
                dangerous_action_failures
            )
        else:
            checks_passed.append(
                "Recovery action passed dangerous-action policy"
            )

        # -------------------------------------------------
        # Final approval decision
        # -------------------------------------------------

        if checks_failed:
            return SafetyEvaluation(
                decision=SafetyDecision.BLOCKED,
                risk_level=action.risk_level,
                checks_passed=checks_passed,
                checks_failed=checks_failed,
                reason=(
                    "Recovery action was blocked by "
                    "the Phase 8 safety gate."
                ),
            )

        return SafetyEvaluation(
            decision=SafetyDecision.APPROVED,
            risk_level=action.risk_level,
            checks_passed=checks_passed,
            checks_failed=[],
            reason=(
                "Recovery action passed the complete "
                "Phase 8 safety gate."
            ),
        )
