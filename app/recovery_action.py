from dataclasses import dataclass, field
from enum import Enum


class RecoveryActionType(str, Enum):
    RESTART_SERVICE = "restart_service"
    RESTORE_SERVICE = "restore_service"
    ROLLBACK_VERSION = "rollback_version"
    REDIRECT_TRAFFIC = "redirect_traffic"
    CLEAR_CACHE = "clear_cache"


class RecoveryRiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RecoveryAction:
    action_type: RecoveryActionType
    target_service: str
    reason: str
    preconditions: list[str] = field(default_factory=list)
    expected_outcomes: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    risk_level: RecoveryRiskLevel = RecoveryRiskLevel.MEDIUM
    parameters: dict = field(default_factory=dict)
