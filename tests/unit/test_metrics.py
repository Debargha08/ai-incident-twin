import pytest

from app.evaluation.metrics import BenchmarkMetricsCalculator


def calculate_metrics(**overrides):
    inputs = {
        "root_cause_results": [True, False],
        "recovery_action_results": [True, True],
        "safety_results": [True, False],
        "execution_results": [True, False],
        "verification_results": [True, False],
        "regression_results": [True, True],
        "recovery_results": [True, False],
        "safety_candidates_evaluated": 4,
        "safety_blocked_candidates": 1,
    }
    inputs.update(overrides)
    return BenchmarkMetricsCalculator().calculate(**inputs)


def test_candidate_safety_block_rate():
    metrics = calculate_metrics()

    assert metrics.safety_candidates_evaluated == 4
    assert metrics.safety_blocked_candidates == 1
    assert metrics.safety_candidate_block_rate == 0.25


def test_candidate_safety_block_rate_with_no_candidates():
    metrics = calculate_metrics(
        safety_candidates_evaluated=0,
        safety_blocked_candidates=0,
    )

    assert metrics.safety_candidate_block_rate == 0.0


def test_blocked_candidates_cannot_exceed_evaluated_candidates():
    with pytest.raises(ValueError):
        calculate_metrics(
            safety_candidates_evaluated=2,
            safety_blocked_candidates=3,
        )


def test_negative_candidate_count_is_rejected():
    with pytest.raises(ValueError):
        calculate_metrics(safety_candidates_evaluated=-1)



def test_recovery_action_accuracy_uses_supplied_action_results():
    metrics = calculate_metrics(
        recovery_action_results=[True, False],
    )

    assert metrics.recovery_action_accuracy == 0.5



def test_candidate_action_coverage_is_aggregated_separately():
    metrics = calculate_metrics(
        recovery_action_results=[False, True],
        candidate_action_results=[True, True],
    )

    assert metrics.recovery_action_accuracy == 0.5
    assert metrics.candidate_action_coverage == 1.0


def test_candidate_action_results_must_match_incident_count():
    with pytest.raises(ValueError):
        calculate_metrics(candidate_action_results=[True])
