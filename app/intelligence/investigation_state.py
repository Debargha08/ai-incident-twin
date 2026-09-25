from dataclasses import dataclass
from enum import Enum


class InvestigationState(str, Enum):
    START = "start"
    COLLECTING_EVIDENCE = "collecting_evidence"
    ANALYZING = "analyzing"
    GENERATING_HYPOTHESES = "generating_hypotheses"
    RANKING_HYPOTHESES = "ranking_hypotheses"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class InvestigationProgress:
    state: InvestigationState = InvestigationState.START
    message: str = ""

    def transition(
        self,
        state: InvestigationState,
        message: str = "",
    ) -> None:
        self.state = state
        self.message = message
