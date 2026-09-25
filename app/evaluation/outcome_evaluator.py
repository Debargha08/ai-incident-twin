from dataclasses import dataclass


@dataclass
class RecoveryOutcomeEvaluation:
    verification_successful: bool
    regression_free: bool
    recovery_successful: bool


class RecoveryOutcomeEvaluator:
    def evaluate(
        self,
        verification_successful: bool,
        regression_free: bool,
    ) -> RecoveryOutcomeEvaluation:
        recovery_successful = (
            verification_successful
            and regression_free
        )

        return RecoveryOutcomeEvaluation(
            verification_successful=verification_successful,
            regression_free=regression_free,
            recovery_successful=recovery_successful,
        )
