from dataclasses import dataclass


@dataclass
class RecoveryActionEvaluation:
    expected_actions: list[str]
    predicted_action: str
    correct: bool


class RecoveryActionEvaluator:
    def evaluate(
        self,
        expected_actions: list[str],
        predicted_action: str,
    ) -> RecoveryActionEvaluation:
        normalized_expected = [
            action.strip().lower()
            for action in expected_actions
        ]

        normalized_predicted = predicted_action.strip().lower()

        return RecoveryActionEvaluation(
            expected_actions=normalized_expected,
            predicted_action=normalized_predicted,
            correct=normalized_predicted in normalized_expected,
        )
