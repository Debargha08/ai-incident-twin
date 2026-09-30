from dataclasses import dataclass


@dataclass
class BenchmarkMetrics:
    total_incidents: int
    root_cause_accuracy: float
    recovery_action_accuracy: float
    safety_approval_rate: float
    execution_success_rate: float
    verification_success_rate: float
    regression_free_rate: float
    recovery_success_rate: float


class BenchmarkMetricsCalculator:
    def calculate(
        self,
        root_cause_results: list[bool],
        recovery_action_results: list[bool],
        safety_results: list[bool],
        execution_results: list[bool],
        verification_results: list[bool],
        regression_results: list[bool],
        recovery_results: list[bool],
    ) -> BenchmarkMetrics:
        total_incidents = len(root_cause_results)

        if total_incidents == 0:
            raise ValueError(
                "At least one benchmark result is required."
            )

        if len(recovery_action_results) != total_incidents:
            raise ValueError(
                "Recovery action results must match incident count."
            )

        if len(safety_results) != total_incidents:
            raise ValueError(
                "Safety results must match incident count."
            )

        if len(execution_results) != total_incidents:
            raise ValueError(
                "Execution results must match incident count."
            )

        if len(verification_results) != total_incidents:
            raise ValueError(
                "Verification results must match incident count."
            )

        if len(regression_results) != total_incidents:
            raise ValueError(
                "Regression results must match incident count."
            )

        if len(recovery_results) != total_incidents:
            raise ValueError(
                "Recovery results must match incident count."
            )

        root_cause_accuracy = (
            sum(root_cause_results) / total_incidents
        )

        recovery_action_accuracy = (
            sum(recovery_action_results) / total_incidents
        )

        safety_approval_rate = (
            sum(safety_results) / total_incidents
        )

        execution_success_rate = (
            sum(execution_results) / total_incidents
        )

        verification_success_rate = (
            sum(verification_results) / total_incidents
        )

        regression_free_rate = (
            sum(regression_results) / total_incidents
        )

        recovery_success_rate = (
            sum(recovery_results) / total_incidents
        )

        return BenchmarkMetrics(
            total_incidents=total_incidents,
            root_cause_accuracy=root_cause_accuracy,
            recovery_action_accuracy=recovery_action_accuracy,
            safety_approval_rate=safety_approval_rate,
            execution_success_rate=execution_success_rate,
            verification_success_rate=verification_success_rate,
            regression_free_rate=regression_free_rate,
            recovery_success_rate=recovery_success_rate,
        )
