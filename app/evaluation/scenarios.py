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
            description="Order service experiences an elevated error rate.",
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
        BenchmarkScenario(
            name="postgresql_crash",
            description="PostgreSQL crashes and affects dependent services.",
            target_service="postgresql",
            failure_type="crash",
            expected_root_cause="postgresql",
            expected_recovery_actions=["restart_service"],
        ),
        BenchmarkScenario(
            name="user_service_crash",
            description="User service crashes independently.",
            target_service="user-service",
            failure_type="crash",
            expected_root_cause="user-service",
            expected_recovery_actions=["restart_service"],
        ),
        BenchmarkScenario(
            name="order_service_latency_spike",
            description="Order service experiences a severe latency increase.",
            target_service="order-service",
            failure_type="latency",
            expected_root_cause="order-service",
            expected_recovery_actions=["restore_service", "restart_service"],
        ),
        BenchmarkScenario(
            name="user_service_latency_spike",
            description="User service experiences a severe latency increase.",
            target_service="user-service",
            failure_type="latency",
            expected_root_cause="user-service",
            expected_recovery_actions=["restore_service", "restart_service"],
        ),
        BenchmarkScenario(
            name="redis_latency_spike",
            description="Redis experiences a severe latency increase.",
            target_service="redis",
            failure_type="latency",
            expected_root_cause="redis",
            expected_recovery_actions=["restore_service", "restart_service"],
        ),
    ]
