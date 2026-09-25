from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class RecoveryExecutionLog:
    timestamp: datetime
    action_type: str
    target_service: str
    success: bool
    message: str

    @classmethod
    def from_result(cls, result):
        return cls(
            timestamp=datetime.now(timezone.utc),
            action_type=result.action_type,
            target_service=result.target_service,
            success=result.success,
            message=result.message,
        )
