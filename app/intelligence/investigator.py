from dataclasses import dataclass, field
import json

from langchain_ollama import ChatOllama

from app.intelligence.investigation_prompt import (
    build_investigation_prompt,
)
from app.intelligence.investigation_state import (
    InvestigationProgress,
    InvestigationState,
)


@dataclass
class RCAHypothesis:
    root_cause: str
    confidence: float
    evidence: list[str] = field(default_factory=list)
    reasoning: str = ""


@dataclass
class InvestigationResult:
    incident_id: str
    hypotheses: list[RCAHypothesis] = field(default_factory=list)
    primary_hypothesis: RCAHypothesis | None = None
    investigation_steps: list[str] = field(default_factory=list)
    raw_response: str = ""
    state: InvestigationState = InvestigationState.START


class AIInvestigator:
    def __init__(self, llm=None) -> None:
        self.llm = llm or ChatOllama(
            model="qwen2.5:7b",
            temperature=0,
        )

    def investigate(self, context) -> InvestigationResult:
        progress = InvestigationProgress()

        try:
            progress.transition(
                InvestigationState.COLLECTING_EVIDENCE,
                "Collected incident evidence",
            )

            prompt = build_investigation_prompt(context)

            progress.transition(
                InvestigationState.ANALYZING,
                "Analyzing incident evidence",
            )

            progress.transition(
                InvestigationState.GENERATING_HYPOTHESES,
                "Generating RCA hypotheses",
            )

            response = self.llm.invoke(prompt)

            raw_response = response.content

            hypotheses = self._parse_hypotheses(
                raw_response
            )

            progress.transition(
                InvestigationState.RANKING_HYPOTHESES,
                "Ranking RCA hypotheses",
            )

            primary_hypothesis = (
                max(
                    hypotheses,
                    key=lambda hypothesis: hypothesis.confidence,
                )
                if hypotheses
                else None
            )

            progress.transition(
                InvestigationState.COMPLETED,
                "Investigation completed",
            )

            return InvestigationResult(
                incident_id=context.incident.incident_id,
                hypotheses=hypotheses,
                primary_hypothesis=primary_hypothesis,
                raw_response=raw_response,
                investigation_steps=[
                    "Built investigation context",
                    "Collected incident evidence",
                    "Analyzed incident evidence",
                    "Generated RCA hypotheses",
                    "Ranked RCA hypotheses",
                ],
                state=progress.state,
            )

        except Exception:
            progress.transition(
                InvestigationState.FAILED,
                "Investigation failed",
            )

            return InvestigationResult(
                incident_id=context.incident.incident_id,
                investigation_steps=[
                    "Investigation failed",
                ],
                state=progress.state,
            )

    def _parse_hypotheses(
        self,
        raw_response: str,
    ) -> list[RCAHypothesis]:
        try:
            data = json.loads(raw_response)
        except json.JSONDecodeError:
            return []

        hypotheses_data = data.get("hypotheses", [])

        hypotheses = []

        for item in hypotheses_data:
            confidence = float(
                item.get("confidence", 0.0)
            )

            confidence = max(
                0.0,
                min(1.0, confidence),
            )

            hypotheses.append(
                RCAHypothesis(
                    root_cause=str(
                        item.get("root_cause", "")
                    ),
                    confidence=confidence,
                    evidence=[
                        str(evidence)
                        for evidence in item.get(
                            "evidence",
                            [],
                        )
                    ],
                    reasoning=str(
                        item.get("reasoning", "")
                    ),
                )
            )

        return hypotheses
