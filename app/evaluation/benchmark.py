from dataclasses import dataclass

from app.evaluation.context_builder import BenchmarkContextBuilder
from app.evaluation.evaluator import BenchmarkEvaluator
from app.evaluation.outcome_evaluator import RecoveryOutcomeEvaluator
from app.evaluation.recovery_evaluator import RecoveryActionEvaluator
from app.evaluation.runner import BenchmarkRunner
from app.intelligence.investigator import AIInvestigator
from app.recovery.executor import RecoveryExecutor
from app.recovery.planner import RecoveryPlanner
from app.recovery.reflection import RecoveryReflector
from app.recovery.regression import RecoveryRegressionDetector
from app.recovery.safety_gate import RecoverySafetyGate
from app.recovery.selector import RecoveryActionSelector
from app.recovery.verifier import RecoveryVerifier
from app.simulation.environment import SimulationEnvironment


@dataclass
class BenchmarkScenarioResult:
    scenario_name: str
    expected_root_cause: str
    predicted_root_cause: str
    root_cause_correct: bool
    candidate_actions: list[str]
    selected_action: str | None
    recovery_action_covered: bool
    verification_successful: bool
    regression_free: bool
    recovery_successful: bool


class IncidentTwinBenchmark:
    def __init__(self) -> None:
        environment = SimulationEnvironment()

        self.runner = BenchmarkRunner(environment)
        self.context_builder = BenchmarkContextBuilder(self.runner)

        self.investigator = AIInvestigator()
        self.planner = RecoveryPlanner()

        self.selector = RecoveryActionSelector(
            safety_gate=RecoverySafetyGate()
        )
        self.executor = RecoveryExecutor()
        self.verifier = RecoveryVerifier()
        self.regression_detector = RecoveryRegressionDetector()
        self.reflector = RecoveryReflector()

        self.root_cause_evaluator = BenchmarkEvaluator()
        self.recovery_action_evaluator = RecoveryActionEvaluator()
        self.outcome_evaluator = RecoveryOutcomeEvaluator()

    def run_scenario(self, scenario):
        run_result, context = self.context_builder.build(
            scenario
        )

        investigation = self.investigator.investigate(
            context
        )

        if investigation.primary_hypothesis is None:
            raise RuntimeError(
                f"Investigation produced no primary hypothesis "
                f"for {scenario.name}"
            )

        known_services = list(
            self.runner.environment.services.keys()
        )

        root_cause_evaluation = (
            self.root_cause_evaluator.evaluate_root_cause(
                expected_root_cause=scenario.expected_root_cause,
                predicted_root_cause=(
                    investigation.primary_hypothesis.root_cause
                ),
                known_services=known_services,
            )
        )

        actions = self.planner.plan(
            investigation,
            known_services=known_services,
        )

        candidate_actions = [
            action.action_type.value
            for action in actions
        ]

        recovery_action_covered = any(
            self.recovery_action_evaluator.evaluate(
                scenario.expected_recovery_actions,
                action.action_type.value,
            ).correct
            for action in actions
        )

        selected_action = self.selector.select(
            actions=actions,
            root_cause_service=(
                root_cause_evaluation.predicted_root_cause
            ),
            environment=self.runner.environment,
        )

        if selected_action is None:
            raise RuntimeError(
                f"No executable recovery action selected "
                f"for {scenario.name}"
            )

        safety_evaluation = self.selector.safety_gate.evaluate(
            selected_action,
            self.runner.environment,
        )

        execution_result = self.executor.execute(
            action=selected_action,
            safety_evaluation=safety_evaluation,
            environment=self.runner.environment,
        )

        self.runner.environment.step()

        verification_result = self.verifier.verify(
            environment=self.runner.environment,
            service_name=selected_action.target_service,
        )

        regression_result = self.regression_detector.detect(
            environment=self.runner.environment,
            affected_services=(
                scenario_target_services(
                    scenario,
                    self.runner.environment,
                )
            ),
        )

        reflection = self.reflector.reflect(
            verification_result,
            regression_result,
        )

        outcome = self.outcome_evaluator.evaluate(
            verification_successful=(
                verification_result.healthy
            ),
            regression_free=(
                regression_result.healthy
            ),
        )

        return BenchmarkScenarioResult(
            scenario_name=scenario.name,
            expected_root_cause=(
                root_cause_evaluation.expected_root_cause
            ),
            predicted_root_cause=(
                root_cause_evaluation.predicted_root_cause
            ),
            root_cause_correct=(
                root_cause_evaluation.correct
            ),
            candidate_actions=candidate_actions,
            selected_action=(
                selected_action.action_type.value
            ),
            recovery_action_covered=(
                recovery_action_covered
            ),
            verification_successful=(
                verification_result.healthy
            ),
            regression_free=(
                regression_result.healthy
            ),
            recovery_successful=(
                outcome.recovery_successful
            ),
        )


def scenario_target_services(
    scenario,
    environment,
) -> list[str]:
    affected_services = [
        scenario.target_service
    ]

    for service in environment.services.values():
        if scenario.target_service in service.dependencies:
            affected_services.append(service.name)

    return sorted(set(affected_services))
