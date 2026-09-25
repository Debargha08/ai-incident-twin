from dataclasses import dataclass, field


@dataclass
class RecoveryReflection:
    recovery_successful: bool
    failed_checks: list[str] = field(default_factory=list)
    observations: list[str] = field(default_factory=list)
    recommended_next_steps: list[str] = field(default_factory=list)
    retry_required: bool = False
    message: str = ""


class RecoveryReflector:
    def reflect(self, verification_result, regression_result=None):
        observations = []
        recommended_next_steps = []

        if verification_result.healthy:
            observations.append(
                "Target service passed recovery verification."
            )
        else:
            observations.append(
                "Target service failed recovery verification."
            )

        failed_checks = list(verification_result.checks_failed)

        if regression_result is not None:
            if regression_result.healthy:
                observations.append(
                    "No recovery regression was detected."
                )
            else:
                observations.append(
                    "Recovery regression was detected."
                )

                recommended_next_steps.append(
                    "Re-investigate affected services."
                )

        if failed_checks:
            recommended_next_steps.append(
                "Review failed recovery verification checks."
            )

        recovery_successful = (
            verification_result.healthy
            and (
                regression_result is None
                or regression_result.healthy
            )
        )

        retry_required = not recovery_successful

        if recovery_successful:
            message = "Recovery was successful and no regression was detected."
        else:
            message = (
                "Recovery was unsuccessful and further investigation "
                "is required."
            )

        return RecoveryReflection(
            recovery_successful=recovery_successful,
            failed_checks=failed_checks,
            observations=observations,
            recommended_next_steps=recommended_next_steps,
            retry_required=retry_required,
            message=message,
        )
