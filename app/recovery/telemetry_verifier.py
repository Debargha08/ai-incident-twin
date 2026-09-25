from dataclasses import dataclass


@dataclass
class TelemetryVerificationResult:
    service: str
    healthy: bool
    checks_passed: list[str]
    checks_failed: list[str]
    message: str


class TelemetryVerifier:
    MAX_LATENCY_MS = 100.0
    MAX_ERROR_RATE = 0.0

    def verify(self, telemetry) -> TelemetryVerificationResult:
        checks_passed = []
        checks_failed = []

        if telemetry.error_rate <= self.MAX_ERROR_RATE:
            checks_passed.append("Telemetry error rate is healthy")
        else:
            checks_failed.append(
                f"Telemetry error rate is {telemetry.error_rate}"
            )

        if telemetry.latency_ms <= self.MAX_LATENCY_MS:
            checks_passed.append("Telemetry latency is healthy")
        else:
            checks_failed.append(
                f"Telemetry latency is {telemetry.latency_ms}ms"
            )

        healthy = len(checks_failed) == 0

        if healthy:
            message = (
                f"Telemetry for '{telemetry.service}' "
                "indicates successful recovery."
            )
        else:
            message = (
                f"Telemetry for '{telemetry.service}' "
                "indicates incomplete recovery."
            )

        return TelemetryVerificationResult(
            service=telemetry.service,
            healthy=healthy,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            message=message,
        )
