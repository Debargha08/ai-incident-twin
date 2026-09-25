from datetime import datetime, timezone

from .models import FailureEvent, ServiceStatus, TelemetrySnapshot
from .services import create_default_services


class SimulationEnvironment:
    def __init__(self) -> None:
        self.services = create_default_services()
        self.time_step = 0
        self.telemetry_history: list[TelemetrySnapshot] = []
        self.failure_history: list[FailureEvent] = []
        self.cache_state: dict[str, bool] = {
            "redis": True,
        }

        self.traffic_routes: dict[str, str] = {
            "user-service": "user-service",
            "order-service": "order-service",
            "payment-service": "payment-service",
        }

        self.recovery_execution_history = []

    def reset(self) -> None:
        self.services = create_default_services()
        self.time_step = 0
        self.telemetry_history = []
        self.failure_history = []
        self.cache_state = {
            "redis": True,
        }

        self.traffic_routes = {
            "user-service": "user-service",
            "order-service": "order-service",
            "payment-service": "payment-service",
        }

        self.recovery_execution_history = []

    def step(self) -> list[TelemetrySnapshot]:
        self.time_step += 1

        self._propagate_dependency_failures()

        snapshots = [
            self._generate_telemetry(service)
            for service in self.services.values()
        ]

        self.telemetry_history.extend(snapshots)

        return snapshots

    def get_recent_telemetry(
        self,
        service_name: str | None = None,
        limit: int = 20,
    ) -> list[TelemetrySnapshot]:
        history = self.telemetry_history

        if service_name is not None:
            history = [
                snapshot
                for snapshot in history
                if snapshot.service == service_name
            ]

        return history[-limit:]

    def record_failure(
        self,
        service_name: str,
        failure_type: str,
        parameters: dict | None = None,
    ) -> None:
        self.failure_history.append(
            FailureEvent(
                timestamp=datetime.now(timezone.utc),
                service=service_name,
                failure_type=failure_type,
                parameters=parameters or {},
            )
        )

    def _propagate_dependency_failures(self) -> None:
        for service in self.services.values():
            if service.status == ServiceStatus.FAILED:
                continue

            failed_dependencies = [
                dependency
                for dependency in service.dependencies
                if self.services[dependency].status == ServiceStatus.FAILED
            ]

            if failed_dependencies:
                service.status = ServiceStatus.DEGRADED
                service.error_rate = 0.25
                service.latency_ms = 150.0
                service.dependency_degraded = True
            elif service.dependency_degraded:
                service.status = ServiceStatus.HEALTHY
                service.error_rate = 0.0
                service.latency_ms = 50.0
                service.dependency_degraded = False

    def _generate_telemetry(self, service) -> TelemetrySnapshot:
        if service.status == ServiceStatus.HEALTHY:
            latency = service.latency_ms
            error_rate = service.error_rate
            cpu_usage = 35.0
            memory_usage = 45.0

        elif service.status == ServiceStatus.DEGRADED:
            latency = service.latency_ms
            error_rate = max(service.error_rate, 0.15)
            cpu_usage = 65.0
            memory_usage = 60.0

        else:
            latency = service.latency_ms * 8
            error_rate = max(service.error_rate, 0.80)
            cpu_usage = 90.0
            memory_usage = 85.0

        return TelemetrySnapshot(
            timestamp=datetime.now(timezone.utc),
            service=service.name,
            latency_ms=latency,
            error_rate=error_rate,
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            request_rate=100.0,
        )
