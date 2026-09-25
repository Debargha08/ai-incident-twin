def normalize_root_cause(
    predicted_root_cause: str,
    known_services: list[str],
) -> str:
    predicted = predicted_root_cause.strip().lower()

    if not predicted:
        return ""

    normalized_services = [
        service.strip().lower()
        for service in known_services
        if service.strip()
    ]

    exact_matches = [
        service
        for service in normalized_services
        if predicted == service
    ]

    if exact_matches:
        return exact_matches[0]

    embedded_matches = [
        service
        for service in normalized_services
        if service in predicted
    ]

    if len(embedded_matches) == 1:
        return embedded_matches[0]

    return predicted
