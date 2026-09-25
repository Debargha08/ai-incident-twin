from dataclasses import dataclass, field


@dataclass
class RecoveryRetryState:
    attempt: int = 0
    max_attempts: int = 2
    retry_required: bool = False
    reinvestigation_required: bool = False
    reasons: list[str] = field(default_factory=list)

    @property
    def retry_allowed(self) -> bool:
        return self.retry_required and self.attempt < self.max_attempts


class RecoveryRetryManager:
    def __init__(self, max_attempts: int = 2):
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")

        self.state = RecoveryRetryState(
            max_attempts=max_attempts
        )

    def request_retry(self, reasons: list[str]) -> RecoveryRetryState:
        self.state.retry_required = True
        self.state.reinvestigation_required = True
        self.state.reasons = list(reasons)
        return self.state

    def start_retry(self) -> RecoveryRetryState:
        if not self.state.retry_allowed:
            return self.state

        self.state.attempt += 1
        self.state.retry_required = False
        self.state.reinvestigation_required = False

        return self.state

    def reset(self) -> None:
        self.state = RecoveryRetryState(
            max_attempts=self.state.max_attempts
        )
