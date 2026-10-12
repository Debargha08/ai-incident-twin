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
    selected_action_correct: bool
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
        self.retry_manager.reset()

        run_result, context = self.context_builder.build(scenario)
        environment = self.runner.environment
        known_services = list(environment.services.keys())

        candidate_actions = []
        selected_action_name = None
        failure_stage = None
        safety_approved = False
        safety_candidates_evaluated = 0
        safety_blocked_candidates = 0
        execution_successful = False
        recovery_action_covered = False
        selected_action_correct = False
        verification_successful = False
        regression_free = False
        root_cause_evaluation = None
        reflection = None
        retry_requested_any = False

        # The initial attempt plus at most max_attempts retries.
        while True:
            # Report outcome fields from the current attempt only.
            root_cause_evaluation = None
            candidate_actions = []
            selected_action_name = None
            failure_stage = None
            safety_approved = False
            execution_successful = False
            selected_action_correct = False
            verification_successful = False
            regression_free = False
            investigation = self.investigator.investigate(context)

            if investigation.primary_hypothesis is None:
                failure_stage = "investigation"
                reflection = self.reflector.reflect(
                    type("Verification", (), {
                        "healthy": False,
                        "checks_failed": ["Investigation produced no hypothesis"],
                    })()
                )

                self.retry_manager.request_retry(
                    ["Investigation produced no hypothesis; re-investigate."]
                )
                retry_requested_any = True

                if not self.retry_manager.state.retry_allowed:
                    break

                self.retry_manager.start_retry()
                context = self.context_builder.build_current_context(
                    scenario.name
                )
                continue


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
                dependency_graph=DependencyGraph(environment.services),
            )

            candidate_actions = [
                action.action_type.value for action in actions
            ]

            safety_evaluations = [
                self.selector.safety_gate.evaluate(action, environment)
                for action in actions
            ]

            safety_candidates_evaluated += len(safety_evaluations)
            safety_blocked_candidates += sum(
                not evaluation.approved
                for evaluation in safety_evaluations
            )

            recovery_action_covered = recovery_action_covered or any(
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
                environment=environment,
            )

            if selected_action is None:
                failure_stage = "selection"
                reflection = self.reflector.reflect(
                    type("Verification", (), {
                        "healthy": False,
                        "checks_failed": [
                            "No safe executable recovery action was selected"
                        ],
                    })()
                )

                self.retry_manager.request_retry(
                    ["No safe recovery action was selected; re-investigate."]
                )
                retry_requested_any = True

                if not self.retry_manager.state.retry_allowed:
                    break

                self.retry_manager.start_retry()
                context = self.context_builder.build_current_context(
                    scenario.name
                )
                continue

            # Re-evaluate the selected action immediately before execution.
            safety_evaluation = self.selector.safety_gate.evaluate(
                selected_action, environment
            )

            if not safety_evaluation.approved:
                failure_stage = "safety"
                reflection = self.reflector.reflect(
                    type("Verification", (), {
                        "healthy": False,
                        "checks_failed": (
                            safety_evaluation.checks_failed
                            or [
                                "Selected recovery action failed "
                                "final safety evaluation"
                            ]
                        ),
                    })()
                )

                self.retry_manager.request_retry(
                    [
                        "Final safety evaluation blocked the "
                        "selected action; re-investigate and "
                        "select a safe alternative."
                    ]
                )
                retry_requested_any = True

                if not self.retry_manager.state.retry_allowed:
                    break

                self.retry_manager.start_retry()
                context = self.context_builder.build_current_context(
                    scenario.name
                )
                continue

            selected_action_name = selected_action.action_type.value
            selected_action_correct = (
                self.recovery_action_evaluator.evaluate(
                    scenario.expected_recovery_actions,
                    selected_action_name,
                ).correct
            )
            safety_approved = True

            execution_result = self.executor.execute(
                action=selected_action,
                safety_evaluation=safety_evaluation,
                environment=environment,
            )
            execution_successful = execution_result.success

            if execution_result.success:
                environment.step()

            verification_result = self.verifier.verify(
                environment=environment,
                service_name=selected_action.target_service,
            )

            regression_result = self.regression_detector.detect(
                environment=environment,
                affected_services=scenario_target_services(
                    scenario, environment
                ),
            )

            reflection = self.reflector.reflect(
                verification_result, regression_result
            )

            verification_successful = verification_result.healthy
            regression_free = regression_result.healthy

            if (
                execution_result.success
                and not reflection.retry_required
            ):
                failure_stage = None
                break

            failure_stage = (
                "execution" if not execution_result.success
                else "verification" if not verification_result.healthy
                else "regression"
            )

            if not reflection.retry_required:
                break

            self.retry_manager.request_retry(
                reflection.recommended_next_steps
                or ["Re-investigate the current incident state."]
            )
            retry_requested_any = True

            if not self.retry_manager.state.retry_allowed:
                break

            self.retry_manager.start_retry()

            # Rebuild evidence from the existing environment. Do not reset
            # the scenario or inject the original failure a second time.
            context = self.context_builder.build_current_context(
                scenario.name
            )

        if root_cause_evaluation is None:
            expected_root_cause = scenario.expected_root_cause
            predicted_root_cause = ""
            root_cause_correct = False
        else:
            expected_root_cause = root_cause_evaluation.expected_root_cause
            predicted_root_cause = root_cause_evaluation.predicted_root_cause
            root_cause_correct = root_cause_evaluation.correct

        outcome = self.outcome_evaluator.evaluate(
            verification_successful=verification_successful,
            regression_free=regression_free,
            execution_successful=execution_successful,
        )

        return BenchmarkScenarioResult(
            scenario_name=scenario.name,
            expected_root_cause=expected_root_cause,
            predicted_root_cause=predicted_root_cause,
            root_cause_correct=root_cause_correct,
            candidate_actions=candidate_actions,
            selected_action=selected_action_name,
            failure_stage=failure_stage,
            safety_approved=safety_approved,
            safety_candidates_evaluated=safety_candidates_evaluated,
            safety_blocked_candidates=safety_blocked_candidates,
            execution_successful=execution_successful,
            recovery_action_covered=recovery_action_covered,
            selected_action_correct=selected_action_correct,
            verification_successful=verification_successful,
            regression_free=regression_free,
            recovery_successful=outcome.recovery_successful,
            retry_requested=retry_requested_any,
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
                result.selected_action_correct
                for result in results
            ],
            candidate_action_results=[
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
            safety_candidates_evaluated=sum(
                result.safety_candidates_evaluated
                for result in results
            ),
            safety_blocked_candidates=sum(
                result.safety_blocked_candidates
                for result in results
            ),
        )

        return results, metrics



def scenario_target_services(
    scenario,
    environment,
) -> list[str]:
    """Return the target service and all transitive dependents."""
    affected_services = {scenario.target_service}
    changed = True

    while changed:
        changed = False

        for service in environment.services.values():
            if (
                service.name not in affected_services
                and any(
                    dependency in affected_services
                    for dependency in service.dependencies
                )
            ):
                affected_services.add(service.name)
                changed = True

    return sorted(affected_services)


if __name__ == "__main__":
    from app.evaluation.scenarios import create_initial_scenarios

    benchmark = IncidentTwinBenchmark()
    results, metrics = benchmark.run_all(create_initial_scenarios())

    for result in results:
        print(
            f"{result.scenario_name}: "
            f"RCA={result.root_cause_correct}, "
            f"CANDIDATE_COVERAGE={result.recovery_action_covered}, "
            f"SELECTED_ACTION_CORRECT={result.selected_action_correct}, "
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
        f"Selected-action accuracy:   "
        f"{metrics.recovery_action_accuracy:.0%}"
    )
    print(
        f"Candidate action coverage:  "
        f"{metrics.candidate_action_coverage:.0%}"
    )
    print(
        f"Safety approval rate:       "
        f"{metrics.safety_approval_rate:.0%}"
    )
    print(
        f"Candidate safety block rate: "
        f"{metrics.safety_candidate_block_rate:.1%}"
    )
    print(
        f"Safety candidates evaluated: "
        f"{metrics.safety_candidates_evaluated}"
    )
    print(
        f"Safety candidates blocked:   "
        f"{metrics.safety_blocked_candidates}"
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
