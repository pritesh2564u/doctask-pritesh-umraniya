from enum import StrEnum


class StageDecision(StrEnum):
    COMPLETE = "complete"
    RETRY = "retry"
    SKIP = "skip"
    ESCALATE = "escalate"
    FAIL = "fail"