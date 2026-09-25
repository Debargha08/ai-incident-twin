from dataclasses import dataclass

from app.evaluation.scenarios import BenchmarkScenario
from app.simulation.environment import SimulationEnvironment
from app.simulation.failures import (
    crash_service,
    degrade_service,
)


@dataclass
class BenchmarkRunResult:
    scenario_name: str
    target_service: str
    failure_type: str
    expected_root_cause: str
    telemetry_collected: bool
    failure_recorded: bool


class BenchmarkRunner:
    def __init__(self, environment: SimulationEnvironment):
        self.environment = environment

    def run(self, scenario: BenchmarkScenario) -> BenchmarkRunResult:
        self.environment.reset()

        if scenario.failure_type == "crash":
            crash_service(
                self.environment,
                scenario.target_service,
            )

        elif scenario.failure_type == "degradation":
            degrade_service(
                self.environment,
                scenario.target_service,
            )

        else:
            raise ValueError(
                f"Unsupported failure type: {scenario.failure_type}"
            )

        self.environment.step()

        telemetry = self.environment.get_recent_telemetry(
            scenario.target_service,
            limit=1,
        )

        failure_recorded = any(
            event.service == scenario.target_service
            for event in self.environment.failure_history
        )

        return BenchmarkRunResult(
            scenario_name=scenario.name,
            target_service=scenario.target_service,
            failure_type=scenario.failure_type,
            expected_root_cause=scenario.expected_root_cause,
            telemetry_collected=bool(telemetry),
            failure_recorded=failure_recorded,
        )
