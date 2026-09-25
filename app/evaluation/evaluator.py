from dataclasses import dataclass

from app.evaluation.root_cause_normalizer import normalize_root_cause


@dataclass
class RootCauseEvaluation:
    expected_root_cause: str
    predicted_root_cause: str
    correct: bool


class BenchmarkEvaluator:
    def evaluate_root_cause(
        self,
        expected_root_cause: str,
        predicted_root_cause: str,
        known_services: list[str] | None = None,
    ) -> RootCauseEvaluation:
        expected = expected_root_cause.strip().lower()

        predicted = predicted_root_cause.strip().lower()

        if known_services:
            predicted = normalize_root_cause(
                predicted,
                known_services,
            )

        return RootCauseEvaluation(
            expected_root_cause=expected,
            predicted_root_cause=predicted,
            correct=expected == predicted,
        )
