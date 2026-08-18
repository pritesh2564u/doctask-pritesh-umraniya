from app.agent.stages import (
    STAGE_ORDER,
    StageName,
    StageStatus,
)


def test_stage_order_is_deterministic():
    assert STAGE_ORDER == [
        StageName.INGEST,
        StageName.EXTRACT,
        StageName.ANALYZE,
        StageName.RECONCILE,
        StageName.REVIEW,
        StageName.COMMIT,
    ]


def test_stage_statuses_include_agent_decisions():
    assert StageStatus.PENDING == "pending"
    assert StageStatus.RUNNING == "running"
    assert StageStatus.COMPLETED == "completed"
    assert StageStatus.FAILED == "failed"
    assert StageStatus.SKIPPED == "skipped"
    assert StageStatus.ESCALATED == "escalated"