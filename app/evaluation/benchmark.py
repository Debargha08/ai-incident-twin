from dataclasses import dataclass

from app.evaluation.context_builder import BenchmarkContextBuilder
from app.evaluation.evaluator import BenchmarkEvaluator
from app.evaluation.metrics import BenchmarkMetricsCalculator
from app.evaluation.outcome_evaluator import RecoveryOutcomeEvaluator
from app.evaluation.recovery_evaluator import RecoveryActionEvaluator
from app.evaluation.runner import BenchmarkRunner
from app.intelligence.investigator import AIInvestigator
from app.intelligence.dependency_graph import DependencyGraph
from app.recovery.executor import RecoveryExecutor
from app.recovery.planner import RecoveryPlanner
from app.recovery.reflection import RecoveryReflector
from app.recovery.retry import RecoveryRetryManager
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
    failure_stage: str | None
    safety_approved: bool
    safety_candidates_evaluated: int
    safety_blocked_candidates: int
    execution_successful: bool
    recovery_action_covered: bool
    verification_successful: bool
    regression_free: bool
    recovery_successful: bool
    retry_requested: bool
    retry_attempts: int


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
        self.retry_manager = RecoveryRetryManager(max_attempts=2)

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
            dependency_graph=DependencyGraph(self.runner.environment.services),
        )

        candidate_actions = [
            action.action_type.value
            for action in actions
        ]

        safety_evaluations = [
            self.selector.safety_gate.evaluate(
                action,
                self.runner.environment,
            )
            for action in actions
        ]

        safety_candidates_evaluated = len(
            safety_evaluations
        )

        safety_blocked_candidates = sum(
            not evaluation.approved
            for evaluation in safety_evaluations
        )

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
            return BenchmarkScenarioResult(
                scenario_name=scenario.name,
                expected_root_cause=root_cause_evaluation.expected_root_cause,
                predicted_root_cause=root_cause_evaluation.predicted_root_cause,
                root_cause_correct=root_cause_evaluation.correct,
                candidate_actions=candidate_actions,
                selected_action=None,
                failure_stage="selection",
                safety_approved=False,
                safety_candidates_evaluated=(
                    safety_candidates_evaluated
                ),
                safety_blocked_candidates=(
                    safety_blocked_candidates
                ),
                execution_successful=False,
                recovery_action_covered=recovery_action_covered,
                verification_successful=False,
                regression_free=False,
                recovery_successful=False,
                retry_requested=False,
                retry_attempts=0,
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

        self.retry_manager.reset()

        if reflection.retry_required:
            self.retry_manager.request_retry(
                reflection.recommended_next_steps
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
            failure_stage=None,
            safety_approved=safety_evaluation.approved,
            safety_candidates_evaluated=(
                safety_candidates_evaluated
            ),
            safety_blocked_candidates=(
                safety_blocked_candidates
            ),
            execution_successful=execution_result.success,
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
            retry_requested=reflection.retry_required,
            retry_attempts=self.retry_manager.state.attempt,
        )


    def run_all(self, scenarios):
        results = [
            self.run_scenario(scenario)
            for scenario in scenarios
        ]

        metrics = BenchmarkMetricsCalculator().calculate(
            root_cause_results=[
                result.root_cause_correct
                for result in results
            ],
            recovery_action_results=[
                result.recovery_action_covered
                for result in results
            ],
            safety_results=[
                result.safety_approved
                for result in results
            ],
            execution_results=[
                result.execution_successful
                for result in results
            ],
            verification_results=[
                result.verification_successful
                for result in results
            ],
            regression_results=[
                result.regression_free
                for result in results
            ],
            recovery_results=[
                result.recovery_successful
                for result in results
            ],
        )

        return results, metrics



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


if __name__ == "__main__":
    from app.evaluation.scenarios import create_initial_scenarios

    benchmark = IncidentTwinBenchmark()
    results, metrics = benchmark.run_all(create_initial_scenarios())

    for result in results:
        print(
            f"{result.scenario_name}: "
            f"RCA={result.root_cause_correct}, "
            f"ACTION={result.recovery_action_covered}, "
            f"SAFETY={result.safety_approved}, "
            f"BLOCKED={result.safety_blocked_candidates}, "
            f"EXECUTION={result.execution_successful}, "
            f"VERIFY={result.verification_successful}, "
            f"REGRESSION={result.regression_free}, "
            f"RECOVERY={result.recovery_successful}, "
            f"RETRY={result.retry_requested}, "
            f"FAILURE={result.failure_stage}"
        )

    print(metrics)

    print("\n===== FINAL BENCHMARK SUMMARY =====")
    print(f"Incidents evaluated:        {metrics.total_incidents}")
    print(
        f"Root-cause accuracy:        "
        f"{metrics.root_cause_accuracy:.0%}"
    )
    print(
        f"Recovery-action accuracy:   "
        f"{metrics.recovery_action_accuracy:.0%}"
    )
    print(
        f"Safety approval rate:       "
        f"{metrics.safety_approval_rate:.0%}"
    )
    print(
        f"Execution success rate:     "
        f"{metrics.execution_success_rate:.0%}"
    )
    print(
        f"Verification success rate:  "
        f"{metrics.verification_success_rate:.0%}"
    )
    print(
        f"Regression-free rate:       "
        f"{metrics.regression_free_rate:.0%}"
    )
    print(
        f"Overall recovery success:   "
        f"{metrics.recovery_success_rate:.0%}"
    )

    total_blocked = sum(
        result.safety_blocked_candidates
        for result in results
    )

    retry_requests = sum(
        result.retry_requested
        for result in results
    )

    print(
        f"Unsafe candidates blocked:   "
        f"{total_blocked}"
    )
    print(
        f"Retry requests:             "
        f"{retry_requests}/{metrics.total_incidents}"
    )
