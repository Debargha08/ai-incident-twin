from dataclasses import dataclass


@dataclass
class RecoveryRegressionResult:
    healthy: bool
    affected_services: list[str]
    unhealthy_services: list[str]
    message: str


class RecoveryRegressionDetector:
    MAX_LATENCY_MS = 100.0
    MAX_ERROR_RATE = 0.0

    def detect(self, environment, affected_services: list[str]) -> RecoveryRegressionResult:
        unhealthy_services = []

        for service_name in affected_services:
            if service_name not in environment.services:
                unhealthy_services.append(service_name)
                continue

            service = environment.services[service_name]

            if service.status.value != "healthy":
                unhealthy_services.append(service_name)
                continue

            if service.error_rate > self.MAX_ERROR_RATE:
                unhealthy_services.append(service_name)
                continue

            if service.latency_ms > self.MAX_LATENCY_MS:
                unhealthy_services.append(service_name)

        healthy = len(unhealthy_services) == 0

        if healthy:
            message = "No recovery regression detected."
        else:
            message = (
                "Recovery regression detected in: "
                + ", ".join(unhealthy_services)
            )

        return RecoveryRegressionResult(
            healthy=healthy,
            affected_services=affected_services,
            unhealthy_services=unhealthy_services,
            message=message,
        )
