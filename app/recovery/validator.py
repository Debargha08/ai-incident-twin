from app.recovery_action import RecoveryAction


def validate_recovery_action(
    action: RecoveryAction,
) -> list[str]:
    """
    Validate that a recovery action contains the
    information required for later safety evaluation.
    """

    errors: list[str] = []

    if not action.target_service.strip():
        errors.append(
            "Recovery action must specify a target service."
        )

    if not action.reason.strip():
        errors.append(
            "Recovery action must specify a reason."
        )

    if not action.preconditions:
        errors.append(
            "Recovery action must define preconditions."
        )

    if not action.expected_outcomes:
        errors.append(
            "Recovery action must define expected outcomes."
        )

    if not isinstance(action.dependencies, list):
        errors.append(
            "Recovery action dependencies must be a list."
        )

    if action.risk_level is None:
        errors.append(
            "Recovery action must specify a risk level."
        )

    return errors


def validate_recovery_actions(
    actions: list[RecoveryAction],
) -> dict[int, list[str]]:
    """
    Validate all candidate recovery actions.

    Returns:
        Mapping of action index to validation errors.
        An empty mapping means all actions are valid.
    """

    validation_errors: dict[int, list[str]] = {}

    for index, action in enumerate(actions, start=1):
        errors = validate_recovery_action(action)

        if errors:
            validation_errors[index] = errors

    return validation_errors
