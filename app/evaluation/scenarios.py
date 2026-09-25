from dataclasses import dataclass, field


@dataclass(frozen=True)
class BenchmarkScenario:
    name: str
    description: str
    target_service: str
    failure_type: str
    expected_root_cause: str
    expected_recovery_actions: list[str] = field(default_factory=list)


def create_initial_scenarios() -> list[BenchmarkScenario]:
    return [
        BenchmarkScenario(
            name="redis_crash",
            description="Redis crashes and causes dependent services to degrade.",
            target_service="redis",
            failure_type="crash",
            expected_root_cause="redis",
            expected_recovery_actions=["restart_service"],
        ),
        BenchmarkScenario(
            name="order_service_degradation",
            description="Order service becomes degraded due to elevated latency.",
            target_service="order-service",
            failure_type="degradation",
            expected_root_cause="order-service",
            expected_recovery_actions=["restore_service", "restart_service"],
        ),
        BenchmarkScenario(
            name="payment_service_crash",
            description="Payment service crashes and affects order processing.",
            target_service="payment-service",
            failure_type="crash",
            expected_root_cause="payment-service",
            expected_recovery_actions=["restart_service"],
        ),
    ]
