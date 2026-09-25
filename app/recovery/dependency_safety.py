def check_dependency_safety(action, environment) -> list[str]:
    """
    Validate the dependency relationships declared by a
    recovery action against the simulation environment.

    Returns a list of dependency-related safety failures.
    """

    failures: list[str] = []

    target_service = action.target_service.strip()

    if target_service not in environment.services:
        failures.append(
            "Target service does not exist"
        )
        return failures

    target = environment.services[target_service]

    for dependency in action.dependencies:

        # Dependency must exist.
        if dependency not in environment.services:
            failures.append(
                f"Dependency does not exist: {dependency}"
            )
            continue

        # A declared dependency should actually depend
        # on the target service being recovered.
        dependency_service = environment.services[dependency]

        if target_service not in dependency_service.dependencies:
            failures.append(
                f"Invalid dependency relationship: "
                f"{dependency} does not depend on "
                f"{target_service}"
            )

    return failures
