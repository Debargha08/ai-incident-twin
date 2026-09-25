from dataclasses import dataclass, field
from enum import Enum

from app.recovery_action import RecoveryRiskLevel


class SafetyDecision(str, Enum):
    APPROVED = "approved"
    BLOCKED = "blocked"


@dataclass
class SafetyEvaluation:
    decision: SafetyDecision
    risk_level: RecoveryRiskLevel
    checks_passed: list[str] = field(
        default_factory=list
    )
    checks_failed: list[str] = field(
        default_factory=list
    )
    reason: str = ""

    @property
    def approved(self) -> bool:
        return self.decision == SafetyDecision.APPROVED
