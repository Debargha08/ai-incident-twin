from app.evaluation.outcome_evaluator import RecoveryOutcomeEvaluator


def test_failed_execution_cannot_count_as_successful_recovery():
    result = RecoveryOutcomeEvaluator().evaluate(
        execution_successful=False,
        verification_successful=True,
        regression_free=True,
    )

    assert result.recovery_successful is False


def test_recovery_requires_execution_verification_and_no_regression():
    evaluator = RecoveryOutcomeEvaluator()

    assert evaluator.evaluate(
        execution_successful=True,
        verification_successful=True,
        regression_free=True,
    ).recovery_successful is True

    assert evaluator.evaluate(
        execution_successful=True,
        verification_successful=False,
        regression_free=True,
    ).recovery_successful is False

    assert evaluator.evaluate(
        execution_successful=True,
        verification_successful=True,
        regression_free=False,
    ).recovery_successful is False
