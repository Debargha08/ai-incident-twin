from types import SimpleNamespace

from app.evaluation import benchmark as benchmark_module
from app.evaluation.benchmark import IncidentTwinBenchmark
from app.evaluation.scenarios import BenchmarkScenario
from app.intelligence.investigator import InvestigationResult, RCAHypothesis
from app.recovery.reflection import RecoveryReflector
from app.recovery.retry import RecoveryRetryManager
from app.recovery_action import RecoveryActionType


def test_run_scenario_retries_after_failed_verification(monkeypatch):
    benchmark = IncidentTwinBenchmark.__new__(IncidentTwinBenchmark)
    benchmark.retry_manager = RecoveryRetryManager(max_attempts=2)

    environment = SimpleNamespace(
        services={"redis": SimpleNamespace(dependencies=[], name="redis")},
        step=lambda: None,
    )
    benchmark.runner = SimpleNamespace(environment=environment)

    context = object()
    context_builder_calls = {"build": 0, "rebuild": 0}

    def build(scenario):
        context_builder_calls["build"] += 1
        return None, context

    def rebuild(scenario_name):
        context_builder_calls["rebuild"] += 1
        return context

    benchmark.context_builder = SimpleNamespace(
        build=build,
        build_current_context=rebuild,
    )

    investigation_calls = {"count": 0}

    def investigate(_context):
        investigation_calls["count"] += 1
        return InvestigationResult(
            incident_id="test-incident",
            primary_hypothesis=RCAHypothesis(
                root_cause="redis",
                confidence=0.95,
            ),
        )

    benchmark.investigator = SimpleNamespace(investigate=investigate)

    action = SimpleNamespace(
        action_type=RecoveryActionType.RESTART_SERVICE,
        target_service="redis",
    )
    benchmark.planner = SimpleNamespace(plan=lambda *args, **kwargs: [action])

    safety_evaluation = SimpleNamespace(approved=True)
    safety_gate = SimpleNamespace(
        evaluate=lambda *args: safety_evaluation
    )
    benchmark.selector = SimpleNamespace(
        safety_gate=safety_gate,
        select=lambda **kwargs: action,
    )

    execution_calls = {"count": 0}

    def execute(**kwargs):
        execution_calls["count"] += 1
        return SimpleNamespace(
            success=execution_calls["count"] == 2
        )

    benchmark.executor = SimpleNamespace(execute=execute)

    verification_calls = {"count": 0}

    def verify(**kwargs):
        verification_calls["count"] += 1
        healthy = verification_calls["count"] == 2
        return SimpleNamespace(
            healthy=healthy,
            checks_failed=[] if healthy else ["Redis remains unhealthy"],
        )

    benchmark.verifier = SimpleNamespace(verify=verify)
    benchmark.regression_detector = SimpleNamespace(
        detect=lambda **kwargs: SimpleNamespace(
            healthy=True,
            affected_services=[],
        )
    )
    benchmark.reflector = RecoveryReflector()

    benchmark.root_cause_evaluator = benchmark_module.BenchmarkEvaluator()
    benchmark.recovery_action_evaluator = (
        benchmark_module.RecoveryActionEvaluator()
    )
    benchmark.outcome_evaluator = (
        benchmark_module.RecoveryOutcomeEvaluator()
    )

    monkeypatch.setattr(
        benchmark_module,
        "DependencyGraph",
        lambda services: object(),
    )
    monkeypatch.setattr(
        benchmark_module,
        "scenario_target_services",
        lambda scenario, environment: ["redis"],
    )

    scenario = BenchmarkScenario(
        name="redis_retry_test",
        description="Test retry after failed verification.",
        target_service="redis",
        failure_type="crash",
        expected_root_cause="redis",
        expected_recovery_actions=["restart_service"],
    )

    result = benchmark.run_scenario(scenario)

    assert result.retry_attempts == 1
    assert result.retry_requested is True
    assert result.execution_successful is True
    assert result.verification_successful is True
    assert result.regression_free is True
    assert result.recovery_successful is True

    assert investigation_calls["count"] == 2
    assert execution_calls["count"] == 2
    assert context_builder_calls == {"build": 1, "rebuild": 1}


def test_run_scenario_stops_after_retry_limit(monkeypatch):
    benchmark = IncidentTwinBenchmark.__new__(IncidentTwinBenchmark)
    benchmark.retry_manager = RecoveryRetryManager(max_attempts=2)

    environment = SimpleNamespace(
        services={"redis": SimpleNamespace(dependencies=[], name="redis")},
        step=lambda: None,
    )
    benchmark.runner = SimpleNamespace(environment=environment)

    context = object()
    context_builder_calls = {"build": 0, "rebuild": 0}

    def build(scenario):
        context_builder_calls["build"] += 1
        return None, context

    def rebuild(scenario_name):
        context_builder_calls["rebuild"] += 1
        return context

    benchmark.context_builder = SimpleNamespace(
        build=build,
        build_current_context=rebuild,
    )

    investigation_calls = {"count": 0}

    def investigate(_context):
        investigation_calls["count"] += 1
        return InvestigationResult(
            incident_id="persistent-failure",
            primary_hypothesis=RCAHypothesis(
                root_cause="redis",
                confidence=0.95,
            ),
        )

    benchmark.investigator = SimpleNamespace(investigate=investigate)

    action = SimpleNamespace(
        action_type=RecoveryActionType.RESTART_SERVICE,
        target_service="redis",
    )
    benchmark.planner = SimpleNamespace(
        plan=lambda *args, **kwargs: [action]
    )

    safety_evaluation = SimpleNamespace(approved=True)
    benchmark.selector = SimpleNamespace(
        safety_gate=SimpleNamespace(
            evaluate=lambda *args: safety_evaluation
        ),
        select=lambda **kwargs: action,
    )

    execution_calls = {"count": 0}

    def execute(**kwargs):
        execution_calls["count"] += 1
        return SimpleNamespace(success=False)

    benchmark.executor = SimpleNamespace(execute=execute)
    benchmark.verifier = SimpleNamespace(
        verify=lambda **kwargs: SimpleNamespace(
            healthy=False,
            checks_failed=["Redis remains unhealthy"],
        )
    )
    benchmark.regression_detector = SimpleNamespace(
        detect=lambda **kwargs: SimpleNamespace(
            healthy=True,
            affected_services=[],
        )
    )
    benchmark.reflector = RecoveryReflector()

    benchmark.root_cause_evaluator = benchmark_module.BenchmarkEvaluator()
    benchmark.recovery_action_evaluator = (
        benchmark_module.RecoveryActionEvaluator()
    )
    benchmark.outcome_evaluator = (
        benchmark_module.RecoveryOutcomeEvaluator()
    )

    monkeypatch.setattr(
        benchmark_module,
        "DependencyGraph",
        lambda services: object(),
    )
    monkeypatch.setattr(
        benchmark_module,
        "scenario_target_services",
        lambda scenario, environment: ["redis"],
    )

    scenario = BenchmarkScenario(
        name="redis_retry_limit_test",
        description="Test retry limit when recovery keeps failing.",
        target_service="redis",
        failure_type="crash",
        expected_root_cause="redis",
        expected_recovery_actions=["restart_service"],
    )

    result = benchmark.run_scenario(scenario)

    # One initial attempt plus two allowed retries.
    assert investigation_calls["count"] == 3
    assert execution_calls["count"] == 3
    assert context_builder_calls == {"build": 1, "rebuild": 2}

    assert result.retry_attempts == 2
    assert result.retry_requested is True
    assert result.execution_successful is False
    assert result.recovery_successful is False


def test_run_scenario_retries_after_investigation_failure(monkeypatch):
    benchmark = IncidentTwinBenchmark.__new__(IncidentTwinBenchmark)
    benchmark.retry_manager = RecoveryRetryManager(max_attempts=2)

    environment = SimpleNamespace(
        services={"redis": SimpleNamespace(dependencies=[], name="redis")},
        step=lambda: None,
    )
    benchmark.runner = SimpleNamespace(environment=environment)

    context = object()
    calls = {"build": 0, "rebuild": 0, "investigate": 0}

    def build(scenario):
        calls["build"] += 1
        return None, context

    def rebuild(scenario_name):
        calls["rebuild"] += 1
        return context

    benchmark.context_builder = SimpleNamespace(
        build=build,
        build_current_context=rebuild,
    )

    def investigate(_context):
        calls["investigate"] += 1
        if calls["investigate"] == 1:
            return InvestigationResult(
                incident_id="investigation-failure",
                primary_hypothesis=None,
            )
        return InvestigationResult(
            incident_id="investigation-recovered",
            primary_hypothesis=RCAHypothesis(
                root_cause="redis",
                confidence=0.95,
            ),
        )

    benchmark.investigator = SimpleNamespace(investigate=investigate)

    action = SimpleNamespace(
        action_type=RecoveryActionType.RESTART_SERVICE,
        target_service="redis",
    )
    benchmark.planner = SimpleNamespace(
        plan=lambda *args, **kwargs: [action]
    )

    safety_evaluation = SimpleNamespace(approved=True)
    benchmark.selector = SimpleNamespace(
        safety_gate=SimpleNamespace(
            evaluate=lambda *args: safety_evaluation
        ),
        select=lambda **kwargs: action,
    )
    benchmark.executor = SimpleNamespace(
        execute=lambda **kwargs: SimpleNamespace(success=True)
    )
    benchmark.verifier = SimpleNamespace(
        verify=lambda **kwargs: SimpleNamespace(
            healthy=True,
            checks_failed=[],
        )
    )
    benchmark.regression_detector = SimpleNamespace(
        detect=lambda **kwargs: SimpleNamespace(
            healthy=True,
            affected_services=[],
        )
    )
    benchmark.reflector = RecoveryReflector()
    benchmark.root_cause_evaluator = benchmark_module.BenchmarkEvaluator()
    benchmark.recovery_action_evaluator = (
        benchmark_module.RecoveryActionEvaluator()
    )
    benchmark.outcome_evaluator = (
        benchmark_module.RecoveryOutcomeEvaluator()
    )

    monkeypatch.setattr(
        benchmark_module, "DependencyGraph", lambda services: object()
    )
    monkeypatch.setattr(
        benchmark_module,
        "scenario_target_services",
        lambda scenario, environment: ["redis"],
    )

    scenario = BenchmarkScenario(
        name="redis_investigation_retry_test",
        description="Retry after an investigation failure.",
        target_service="redis",
        failure_type="crash",
        expected_root_cause="redis",
        expected_recovery_actions=["restart_service"],
    )

    result = benchmark.run_scenario(scenario)

    assert calls == {"build": 1, "rebuild": 1, "investigate": 2}
    assert result.retry_attempts == 1
    assert result.retry_requested is True
    assert result.execution_successful is True
    assert result.recovery_successful is True


def test_run_scenario_retries_after_selection_failure(monkeypatch):
    benchmark = IncidentTwinBenchmark.__new__(IncidentTwinBenchmark)
    benchmark.retry_manager = RecoveryRetryManager(max_attempts=2)

    environment = SimpleNamespace(
        services={"redis": SimpleNamespace(dependencies=[], name="redis")},
        step=lambda: None,
    )
    benchmark.runner = SimpleNamespace(environment=environment)

    context = object()
    calls = {"build": 0, "rebuild": 0, "investigate": 0, "select": 0}

    def build(scenario):
        calls["build"] += 1
        return None, context

    def rebuild(scenario_name):
        calls["rebuild"] += 1
        return context

    benchmark.context_builder = SimpleNamespace(
        build=build,
        build_current_context=rebuild,
    )

    def investigate(_context):
        calls["investigate"] += 1
        return InvestigationResult(
            incident_id="selection-retry",
            primary_hypothesis=RCAHypothesis(
                root_cause="redis",
                confidence=0.95,
            ),
        )

    benchmark.investigator = SimpleNamespace(investigate=investigate)

    action = SimpleNamespace(
        action_type=RecoveryActionType.RESTART_SERVICE,
        target_service="redis",
    )
    benchmark.planner = SimpleNamespace(
        plan=lambda *args, **kwargs: [action]
    )

    safety_evaluation = SimpleNamespace(approved=True)

    def select(**kwargs):
        calls["select"] += 1
        return None if calls["select"] == 1 else action

    benchmark.selector = SimpleNamespace(
        safety_gate=SimpleNamespace(
            evaluate=lambda *args: safety_evaluation
        ),
        select=select,
    )
    execution_calls = {"count": 0}

    def execute(**kwargs):
        execution_calls["count"] += 1
        return SimpleNamespace(success=True)

    benchmark.executor = SimpleNamespace(execute=execute)
    benchmark.verifier = SimpleNamespace(
        verify=lambda **kwargs: SimpleNamespace(
            healthy=True,
            checks_failed=[],
        )
    )
    benchmark.regression_detector = SimpleNamespace(
        detect=lambda **kwargs: SimpleNamespace(
            healthy=True,
            affected_services=[],
        )
    )
    benchmark.reflector = RecoveryReflector()
    benchmark.root_cause_evaluator = benchmark_module.BenchmarkEvaluator()
    benchmark.recovery_action_evaluator = (
        benchmark_module.RecoveryActionEvaluator()
    )
    benchmark.outcome_evaluator = (
        benchmark_module.RecoveryOutcomeEvaluator()
    )

    monkeypatch.setattr(
        benchmark_module, "DependencyGraph", lambda services: object()
    )
    monkeypatch.setattr(
        benchmark_module,
        "scenario_target_services",
        lambda scenario, environment: ["redis"],
    )

    scenario = BenchmarkScenario(
        name="redis_selection_retry_test",
        description="Retry when no action is selected initially.",
        target_service="redis",
        failure_type="crash",
        expected_root_cause="redis",
        expected_recovery_actions=["restart_service"],
    )

    result = benchmark.run_scenario(scenario)

    assert calls == {
        "build": 1,
        "rebuild": 1,
        "investigate": 2,
        "select": 2,
    }
    assert execution_calls["count"] == 1
    assert result.retry_attempts == 1
    assert result.retry_requested is True
    assert result.execution_successful is True
    assert result.recovery_successful is True


def test_run_scenario_retries_after_safety_rejection(monkeypatch):
    benchmark = IncidentTwinBenchmark.__new__(IncidentTwinBenchmark)
    benchmark.retry_manager = RecoveryRetryManager(max_attempts=2)

    environment = SimpleNamespace(
        services={"redis": SimpleNamespace(dependencies=[], name="redis")},
        step=lambda: None,
    )
    benchmark.runner = SimpleNamespace(environment=environment)

    context = object()
    calls = {"build": 0, "rebuild": 0, "investigate": 0, "select": 0}

    def build(scenario):
        calls["build"] += 1
        return None, context

    def rebuild(scenario_name):
        calls["rebuild"] += 1
        return context

    benchmark.context_builder = SimpleNamespace(
        build=build,
        build_current_context=rebuild,
    )

    def investigate(_context):
        calls["investigate"] += 1
        return InvestigationResult(
            incident_id=f"safety-retry-{calls['investigate']}",
            primary_hypothesis=RCAHypothesis(
                root_cause="redis",
                confidence=0.95,
            ),
        )

    benchmark.investigator = SimpleNamespace(investigate=investigate)

    blocked_action = SimpleNamespace(
        action_type=RecoveryActionType.RESTART_SERVICE,
        target_service="redis",
    )
    safe_action = SimpleNamespace(
        action_type=RecoveryActionType.CLEAR_CACHE,
        target_service="redis",
    )

    benchmark.planner = SimpleNamespace(
        plan=lambda *args, **kwargs: [blocked_action, safe_action]
    )

    safety_calls = {"blocked_action": 0}

    def evaluate(action, _environment):
        if action is blocked_action:
            safety_calls["blocked_action"] += 1
            # First call is candidate screening; second is the final check.
            if safety_calls["blocked_action"] == 2:
                return SimpleNamespace(
                    approved=False,
                    checks_failed=["Action blocked by final safety policy"],
                )
        return SimpleNamespace(approved=True, checks_failed=[])

    def select(**kwargs):
        calls["select"] += 1
        return blocked_action if calls["select"] == 1 else safe_action

    benchmark.selector = SimpleNamespace(
        safety_gate=SimpleNamespace(evaluate=evaluate),
        select=select,
    )

    executed_actions = []

    def execute(**kwargs):
        executed_actions.append(kwargs["action"])
        return SimpleNamespace(success=True)

    benchmark.executor = SimpleNamespace(execute=execute)
    benchmark.verifier = SimpleNamespace(
        verify=lambda **kwargs: SimpleNamespace(
            healthy=True,
            checks_failed=[],
        )
    )
    benchmark.regression_detector = SimpleNamespace(
        detect=lambda **kwargs: SimpleNamespace(
            healthy=True,
            affected_services=[],
        )
    )
    benchmark.reflector = RecoveryReflector()
    benchmark.root_cause_evaluator = benchmark_module.BenchmarkEvaluator()
    benchmark.recovery_action_evaluator = (
        benchmark_module.RecoveryActionEvaluator()
    )
    benchmark.outcome_evaluator = (
        benchmark_module.RecoveryOutcomeEvaluator()
    )

    monkeypatch.setattr(
        benchmark_module, "DependencyGraph", lambda services: object()
    )
    monkeypatch.setattr(
        benchmark_module,
        "scenario_target_services",
        lambda scenario, environment: ["redis"],
    )

    scenario = BenchmarkScenario(
        name="redis_safety_retry_test",
        description="Retry after final safety rejection.",
        target_service="redis",
        failure_type="crash",
        expected_root_cause="redis",
        expected_recovery_actions=["clear_cache"],
    )

    result = benchmark.run_scenario(scenario)

    assert blocked_action not in executed_actions
    assert executed_actions == [safe_action]
    assert calls["investigate"] == 2
    assert calls["rebuild"] == 1
    assert result.retry_attempts == 1
    assert result.retry_requested is True
    assert result.execution_successful is True
    assert result.recovery_successful is True


def test_run_scenario_fails_when_execution_succeeds_but_service_stays_unhealthy(
    monkeypatch,
):
    benchmark = IncidentTwinBenchmark.__new__(IncidentTwinBenchmark)
    benchmark.retry_manager = RecoveryRetryManager(max_attempts=2)

    environment = SimpleNamespace(
        services={"redis": SimpleNamespace(dependencies=[], name="redis")},
        step=lambda: None,
    )
    benchmark.runner = SimpleNamespace(environment=environment)

    context = object()
    context_builder_calls = {"build": 0, "rebuild": 0}

    def build(scenario):
        context_builder_calls["build"] += 1
        return None, context

    def rebuild(scenario_name):
        context_builder_calls["rebuild"] += 1
        return context

    benchmark.context_builder = SimpleNamespace(
        build=build,
        build_current_context=rebuild,
    )

    investigation_calls = {"count": 0}

    def investigate(_context):
        investigation_calls["count"] += 1
        return InvestigationResult(
            incident_id="persistent-unhealthy-service",
            primary_hypothesis=RCAHypothesis(
                root_cause="redis",
                confidence=0.95,
            ),
        )

    benchmark.investigator = SimpleNamespace(investigate=investigate)

    action = SimpleNamespace(
        action_type=RecoveryActionType.RESTART_SERVICE,
        target_service="redis",
    )
    benchmark.planner = SimpleNamespace(
        plan=lambda *args, **kwargs: [action]
    )

    safety_evaluation = SimpleNamespace(approved=True)
    benchmark.selector = SimpleNamespace(
        safety_gate=SimpleNamespace(
            evaluate=lambda *args: safety_evaluation
        ),
        select=lambda **kwargs: action,
    )

    execution_calls = {"count": 0}

    def execute(**kwargs):
        execution_calls["count"] += 1
        return SimpleNamespace(success=True)

    benchmark.executor = SimpleNamespace(execute=execute)

    verification_calls = {"count": 0}

    def verify(**kwargs):
        verification_calls["count"] += 1
        return SimpleNamespace(
            healthy=False,
            checks_failed=["Redis remains unhealthy"],
        )

    benchmark.verifier = SimpleNamespace(verify=verify)
    benchmark.regression_detector = SimpleNamespace(
        detect=lambda **kwargs: SimpleNamespace(
            healthy=False,
            affected_services=["redis"],
        )
    )
    benchmark.reflector = RecoveryReflector()

    benchmark.root_cause_evaluator = benchmark_module.BenchmarkEvaluator()
    benchmark.recovery_action_evaluator = (
        benchmark_module.RecoveryActionEvaluator()
    )
    benchmark.outcome_evaluator = (
        benchmark_module.RecoveryOutcomeEvaluator()
    )

    monkeypatch.setattr(
        benchmark_module, "DependencyGraph", lambda services: object()
    )
    monkeypatch.setattr(
        benchmark_module,
        "scenario_target_services",
        lambda scenario, environment: ["redis"],
    )

    scenario = BenchmarkScenario(
        name="persistent_unhealthy_redis",
        description="Restart executes but Redis remains unhealthy.",
        target_service="redis",
        failure_type="crash",
        expected_root_cause="redis",
        expected_recovery_actions=["restart_service"],
    )

    result = benchmark.run_scenario(scenario)

    # One initial attempt plus two retries.
    assert investigation_calls["count"] == 3
    assert execution_calls["count"] == 3
    assert verification_calls["count"] == 3
    assert context_builder_calls == {"build": 1, "rebuild": 2}

    # Successful execution must not imply successful recovery.
    assert result.execution_successful is True
    assert result.verification_successful is False
    assert result.regression_free is False
    assert result.recovery_successful is False
    assert result.retry_requested is True
    assert result.retry_attempts == 2
    assert result.failure_stage == "verification"



def test_candidate_coverage_does_not_imply_selected_action_correctness():
    from app.evaluation.scenarios import BenchmarkScenario
    from app.recovery_action import RecoveryActionType

    scenario = BenchmarkScenario(
        name="action_metric_regression",
        description="Candidate contains an expected action but selector chooses another.",
        target_service="redis",
        failure_type="crash",
        expected_root_cause="redis",
        expected_recovery_actions=["restart_service"],
    )

    benchmark = IncidentTwinBenchmark()
    benchmark.context_builder.build = lambda scenario: (
        None,
        object(),
    )
    benchmark.context_builder.build_current_context = lambda name: object()

    hypothesis = type(
        "Hypothesis",
        (),
        {"root_cause": "redis"},
    )()
    benchmark.investigator.investigate = lambda context: type(
        "Investigation",
        (),
        {"primary_hypothesis": hypothesis},
    )()

    expected_candidate = type(
        "Action",
        (),
        {
            "action_type": RecoveryActionType.RESTART_SERVICE,
            "target_service": "redis",
        },
    )()
    selected_candidate = type(
        "Action",
        (),
        {
            "action_type": RecoveryActionType.CLEAR_CACHE,
            "target_service": "redis",
        },
    )()
    benchmark.planner.plan = lambda *args, **kwargs: [
        expected_candidate,
        selected_candidate,
    ]

    # The planner proposes an expected action, but the selector chooses
    # a different action. Coverage must not imply selection correctness.
    benchmark.selector.select = lambda **kwargs: selected_candidate
    benchmark.selector.safety_gate.evaluate = lambda action, environment: type(
        "SafetyResult",
        (),
        {"approved": True, "checks_failed": []},
    )()

    benchmark.executor.execute = lambda **kwargs: type(
        "ExecutionResult",
        (),
        {"success": False},
    )()

    result = benchmark.run_scenario(scenario)

    assert result.recovery_action_covered is True
    assert result.selected_action_correct is False




def test_retry_outcome_does_not_retain_previous_attempt_success(
    monkeypatch,
):
    benchmark = IncidentTwinBenchmark.__new__(IncidentTwinBenchmark)
    benchmark.retry_manager = RecoveryRetryManager(max_attempts=1)

    environment = SimpleNamespace(
        services={"redis": SimpleNamespace(dependencies=[], name="redis")},
        step=lambda: None,
    )
    benchmark.runner = SimpleNamespace(environment=environment)
    context = object()
    benchmark.context_builder = SimpleNamespace(
        build=lambda scenario: (None, context),
        build_current_context=lambda scenario_name: context,
    )

    calls = {"investigate": 0, "execute": 0, "verify": 0}

    def investigate(_context):
        calls["investigate"] += 1
        if calls["investigate"] == 2:
            return InvestigationResult(
                incident_id="retry-investigation-failure",
                primary_hypothesis=None,
            )
        return InvestigationResult(
            incident_id="initial-attempt",
            primary_hypothesis=RCAHypothesis(
                root_cause="redis", confidence=0.95
            ),
        )

    benchmark.investigator = SimpleNamespace(investigate=investigate)

    action = SimpleNamespace(
        action_type=RecoveryActionType.RESTART_SERVICE,
        target_service="redis",
    )
    benchmark.planner = SimpleNamespace(
        plan=lambda *args, **kwargs: [action]
    )
    safety_evaluation = SimpleNamespace(approved=True, checks_failed=[])
    benchmark.selector = SimpleNamespace(
        safety_gate=SimpleNamespace(
            evaluate=lambda *args: safety_evaluation
        ),
        select=lambda **kwargs: action,
    )

    def execute(**kwargs):
        calls["execute"] += 1
        return SimpleNamespace(success=True)

    def verify(**kwargs):
        calls["verify"] += 1
        return SimpleNamespace(
            healthy=False,
            checks_failed=["Redis remains unhealthy"],
        )

    benchmark.executor = SimpleNamespace(execute=execute)
    benchmark.verifier = SimpleNamespace(verify=verify)
    benchmark.regression_detector = SimpleNamespace(
        detect=lambda **kwargs: SimpleNamespace(
            healthy=True, affected_services=["redis"]
        )
    )
    benchmark.reflector = RecoveryReflector()
    benchmark.root_cause_evaluator = benchmark_module.BenchmarkEvaluator()
    benchmark.recovery_action_evaluator = (
        benchmark_module.RecoveryActionEvaluator()
    )
    benchmark.outcome_evaluator = benchmark_module.RecoveryOutcomeEvaluator()

    monkeypatch.setattr(
        benchmark_module, "DependencyGraph", lambda services: object()
    )
    monkeypatch.setattr(
        benchmark_module,
        "scenario_target_services",
        lambda scenario, environment: ["redis"],
    )

    scenario = BenchmarkScenario(
        name="retry_state_reset_test",
        description="Failed verification followed by failed investigation.",
        target_service="redis",
        failure_type="crash",
        expected_root_cause="redis",
        expected_recovery_actions=["restart_service"],
    )

    result = benchmark.run_scenario(scenario)

    assert calls == {"investigate": 2, "execute": 1, "verify": 1}
    assert result.retry_attempts == 1
    assert result.root_cause_correct is False
    assert result.selected_action is None
    assert result.safety_approved is False
    assert result.execution_successful is False
    assert result.verification_successful is False
    assert result.regression_free is False
    assert result.recovery_successful is False
