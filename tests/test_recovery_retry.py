import pytest

from app.recovery.retry import RecoveryRetryManager


def test_retry_starts_after_request():
    manager = RecoveryRetryManager(max_attempts=2)

    state = manager.request_retry(["Verification failed"])

    assert state.retry_required is True
    assert state.reinvestigation_required is True
    assert state.retry_allowed is True
    assert state.attempt == 0

    state = manager.start_retry()

    assert state.attempt == 1
    assert state.retry_required is False
    assert state.reinvestigation_required is False


def test_retry_limit_is_enforced():
    manager = RecoveryRetryManager(max_attempts=2)

    manager.request_retry(["First attempt failed"])
    manager.start_retry()

    manager.request_retry(["Second attempt failed"])
    manager.start_retry()

    manager.request_retry(["Third attempt failed"])
    state = manager.start_retry()

    assert state.attempt == 2
    assert state.retry_required is True
    assert state.retry_allowed is False


def test_retry_reasons_are_preserved():
    manager = RecoveryRetryManager(max_attempts=2)
    reasons = ["Verification failed", "Regression detected"]

    state = manager.request_retry(reasons)

    assert state.reasons == reasons
    assert state.reasons is not reasons


def test_reset_clears_attempt_state_and_preserves_limit():
    manager = RecoveryRetryManager(max_attempts=3)

    manager.request_retry(["Verification failed"])
    manager.start_retry()
    manager.reset()

    assert manager.state.attempt == 0
    assert manager.state.max_attempts == 3
    assert manager.state.retry_required is False
    assert manager.state.reinvestigation_required is False
    assert manager.state.reasons == []


def test_invalid_retry_limit_is_rejected():
    with pytest.raises(ValueError):
        RecoveryRetryManager(max_attempts=0)
