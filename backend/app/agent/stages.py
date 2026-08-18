from enum import StrEnum


class StageName(StrEnum):
    INGEST = "ingest"
    EXTRACT = "extract"
    ANALYZE = "analyze"
    RECONCILE = "reconcile"
    REVIEW = "review"
    COMMIT = "commit"


class StageStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ESCALATED = "escalated"


STAGE_ORDER = [
    StageName.INGEST,
    StageName.EXTRACT,
    StageName.ANALYZE,
    StageName.RECONCILE,
    StageName.REVIEW,
    StageName.COMMIT,
]