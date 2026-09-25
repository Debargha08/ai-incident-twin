from app.intelligence.incident_context import IncidentContext


def build_investigation_prompt(
    context: IncidentContext,
) -> str:
    lines = []

    lines.append("You are an AI production incident investigator.")
    lines.append("")
    lines.append(
        "Analyze the incident using only the observable evidence provided."
    )
    lines.append(
        "Do not use hidden ground truth or information not present in the evidence."
    )
    lines.append(
        "Identify the most likely root cause and alternative hypotheses."
    )
    lines.append("ROOT CAUSE EVIDENCE RULES")
    lines.append(
        "The root cause must be supported by observed anomalies, symptoms, logs, traces, or metrics."
    )
    lines.append(
        "A dependency listed under a service is topology information, NOT evidence that the dependency is failing."
    )
    lines.append(
        "Never select a dependency as the root cause unless that dependency has its own observable anomaly or failure evidence."
    )
    lines.append(
        "If only one service has observable anomalies, that service must be the primary root-cause hypothesis."
    )
    lines.append(
        "For this incident, do not infer a root cause from the dependency graph alone."
    )
    lines.append("")
    lines.append("")

    lines.append("IMPORTANT OUTPUT FORMAT")
    lines.append(
        "Return ONLY valid JSON. Do not use Markdown."
    )
    lines.append(
        "Do not include explanations outside the JSON object."
    )
    lines.append("")
    lines.append(
        "Use exactly this structure:"
    )
    lines.append(
        '{"hypotheses": ['
        '{"root_cause": "string", '
        '"confidence": 0.0, '
        '"evidence": ["string"], '
        '"reasoning": "string"}'
        ']}'
    )
    lines.append("")
    lines.append(
        "The confidence value must be between 0 and 1."
    )
    lines.append(
        "Provide at least 2 hypotheses when the evidence supports alternatives."
    )
    lines.append("")

    lines.append("INCIDENT")
    lines.append(f"ID: {context.incident.incident_id}")
    lines.append(f"Severity: {context.incident.severity.value}")
    lines.append(f"Status: {context.incident.status.value}")
    lines.append(
        "Affected services: "
        + ", ".join(context.incident.affected_services)
    )
    lines.append("")

    lines.append("SYMPTOMS")
    for symptom in context.incident.symptoms:
        lines.append(f"- {symptom}")
    lines.append("")

    lines.append("SERVICE EVIDENCE")

    for service in context.evidence.services:
        lines.append("")
        lines.append(f"Service: {service.service}")
        lines.append(
            f"Anomaly count: {service.anomaly_count}"
        )

        if service.symptoms:
            lines.append("Symptoms:")
            for symptom in service.symptoms:
                lines.append(f"- {symptom}")

        if service.log_levels:
            lines.append(
                "Log levels: "
                + ", ".join(service.log_levels)
            )

        if service.trace_statuses:
            lines.append(
                "Trace statuses: "
                + ", ".join(service.trace_statuses)
            )

        if service.trace_durations_ms:
            durations = ", ".join(
                f"{duration:.1f}ms"
                for duration in service.trace_durations_ms
            )
            lines.append(
                f"Trace durations: {durations}"
            )

        if service.dependencies:
            lines.append(
                "Dependencies: "
                + ", ".join(service.dependencies)
            )

        if service.dependents:
            lines.append(
                "Dependents: "
                + ", ".join(service.dependents)
            )

    lines.append("")
    lines.append("INVESTIGATION TASK")
    lines.append(
        "Determine the most likely root cause."
    )
    lines.append(
        "Provide alternative hypotheses."
    )
    lines.append(
        "Support each hypothesis with concrete evidence."
    )
    lines.append(
        "Assign a confidence value between 0 and 1."
    )
    lines.append("")
    lines.append(
        "Return ONLY the JSON object described above."
    )

    return "\n".join(lines)
