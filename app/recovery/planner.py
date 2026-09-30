import json
import re

from langchain_ollama import ChatOllama
from app.intelligence.dependency_graph import DependencyGraph

from app.recovery_action import (
    RecoveryAction,
    RecoveryActionType,
    RecoveryRiskLevel,
)


class RecoveryPlanner:
    def __init__(self, llm=None) -> None:
        self.llm = llm or ChatOllama(
            model="qwen2.5:7b",
            temperature=0,
        )

    def plan(self, investigation_result, known_services=None, dependency_graph=None):
        prompt = self._build_prompt(
            investigation_result,
            known_services or [],
            dependency_graph=dependency_graph,
        )

        response = self.llm.invoke(prompt)

        return self._parse_actions(
            response.content,
            dependency_graph=dependency_graph,
        )

    def _build_prompt(self, result, known_services, dependency_graph=None) -> str:
        primary = result.primary_hypothesis

        lines = [
            "You are an AI production recovery planner.",
            "",
            "Create safe candidate recovery actions based only",
            "on the investigation result provided.",
            "",
            "Do not execute any action.",
            "Only propose recovery actions.",
            "",
            "Return ONLY valid JSON using this structure:",
            '{"actions": ['
            '{"action_type": "restart_service", '
            '"target_service": "redis", '
            '"reason": "string", '
            '"preconditions": ["string"], '
            '"expected_outcomes": ["string"], '
            '"dependencies": ["string"], '
            '"risk_level": "medium"}'
            ']}',
            "",
            "Allowed action types:",
            "- restart_service",
            "- restore_service",
            "- rollback_version",
            "- redirect_traffic",
            "- clear_cache",
            "",
            "Allowed risk levels:",
            "- low",
            "- medium",
            "- high",
            "- critical",
            "",
            "Dependency field rules:",
            "- dependencies represent services that depend on the target service being recovered.",
            "- Use the dependency topology to identify those dependent services.",
            "- Do not list services that the target service itself depends on.",
            "- Include only exact service names from the known services list.",
            "- Do not put explanations, conditions, or sentences in dependencies.",
            "- Use an empty list when no known service depends on the target service.",
            "Known services:",
            *[f"- {service}" for service in known_services],
            "",
            f"Primary root cause: {primary.root_cause}",
            f"Confidence: {primary.confidence}",
            "",
            "Evidence:",
        ]

        for evidence in primary.evidence:
            lines.append(f"- {evidence}")

        lines.extend(
            [
                "",
                "Reasoning:",
                primary.reasoning,
                "",
                "Propose 2 to 4 candidate recovery actions.",
                "Consider dependencies and service impact.",
                "Every action must include preconditions.",
                "Every action must include expected outcomes.",
                "Assign a realistic risk level.",
                "",
                "Return ONLY the JSON object.",
            ]
        )

        return "\n".join(lines)

    def _parse_actions(
        self,
        raw_response: str,
        dependency_graph=None,
    ) -> list[RecoveryAction]:
        cleaned = raw_response.strip()

        # Remove Markdown code fences.
        cleaned = re.sub(
            r"^```(?:json)?\s*",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )

        cleaned = re.sub(
            r"\s*```$",
            "",
            cleaned,
        )

        cleaned = cleaned.strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            return []

        raw_actions = data.get("actions", [])

        if not isinstance(raw_actions, list):
            return []

        actions: list[RecoveryAction] = []

        for item in raw_actions:
            if not isinstance(item, dict):
                continue

            try:
                action_type = RecoveryActionType(
                    str(item["action_type"]).strip()
                )

                risk_level = RecoveryRiskLevel(
                    str(
                        item.get(
                            "risk_level",
                            "medium",
                        )
                    ).strip()
                )

                actions.append(
                    RecoveryAction(
                        action_type=action_type,
                        target_service=str(
                            item.get(
                                "target_service",
                                "",
                            )
                        ).strip(),
                        reason=str(
                            item.get(
                                "reason",
                                "",
                            )
                        ).strip(),
                        preconditions=[
                            str(value)
                            for value in item.get(
                                "preconditions",
                                [],
                            )
                        ],
                        expected_outcomes=[
                            str(value)
                            for value in item.get(
                                "expected_outcomes",
                                [],
                            )
                        ],
                        dependencies=[
                            str(value)
                            for value in item.get(
                                "dependencies",
                                [],
                            )
                        ],
                        risk_level=risk_level,
                    )
                )
                if dependency_graph is not None:
                    actions[-1].dependencies = dependency_graph.dependents_of(
                        actions[-1].target_service
                    )

            except (
                KeyError,
                ValueError,
                TypeError,
            ):
                continue

        return actions
