from dataclasses import dataclass


@dataclass
class RecoveryVerificationResult:
    service: str
    healthy: bool
    checks_passed: list[str]
    checks_failed: list[str]
    message: str


class RecoveryVerifier:
    def verify(self, environment, service_name: str) -> RecoveryVerificationResult:
        if service_name not in environment.services:
            return RecoveryVerificationResult(
                service=service_name,
                healthy=False,
                checks_passed=[],
                checks_failed=["Service does not exist"],
                message=f"Service '{service_name}' was not found.",
            )

        service = environment.services[service_name]

        checks_passed = []
        checks_failed = []

        if service.status.value == "healthy":
            checks_passed.append("Service status is healthy")
        else:
            checks_failed.append(
                f"Service status is {service.status.value}"
            )

        if service.error_rate == 0.0:
            checks_passed.append("Error rate is zero")
        else:
            checks_failed.append(
                f"Error rate is {service.error_rate}"
            )

        if service.latency_ms <= 100.0:
            checks_passed.append("Latency is within healthy range")
        else:
            checks_failed.append(
                f"Latency is {service.latency_ms}ms"
            )

        healthy = len(checks_failed) == 0

        if healthy:
            message = (
                f"Service '{service_name}' passed all recovery "
                "verification checks."
            )
        else:
            message = (
                f"Service '{service_name}' failed recovery "
                "verification."
            )

        return RecoveryVerificationResult(
            service=service_name,
            healthy=healthy,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            message=message,
        )
