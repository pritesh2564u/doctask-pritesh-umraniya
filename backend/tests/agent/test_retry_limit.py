from uuid import uuid4

import pytest

from app.agent.decisions import StageDecision
from app.agent.executor import (
    MAX_STAGE_ATTEMPTS,
    WorkflowExecutor,
)
from app.agent.stage_handlers import StageResult
from app.agent.stages import StageName, StageStatus
from app.models.project import Project
from app.models.run import Run


@pytest.mark.asyncio
async def test_stage_retry_limit_fails_run(
    db_session,
    monkeypatch,
):
    project = Project(
        name=f"Retry Limit Test {uuid4()}",
    )

    db_session.add(project)
    await db_session.flush()

    executor = WorkflowExecutor()

    run = await executor.run_service.create_run(
        db_session,
        project.id,
    )

    async def always_retry(
        db,
        project_id,
        run_id,
        stage,
    ):
        return StageResult(
            decision=StageDecision.RETRY,
            message="Temporary failure",
            data={},
        )

    monkeypatch.setattr(
        executor.handler,
        "execute",
        always_retry,
    )

    # --------------------------------------------------
    # Retry until the maximum attempt count is reached.
    # --------------------------------------------------

    for _ in range(MAX_STAGE_ATTEMPTS):
        result = await executor.execute_next(
            db=db_session,
            run_id=run.id,
        )

    # --------------------------------------------------
    # The final retry must become FAIL.
    # --------------------------------------------------

    assert result.decision == StageDecision.FAIL

    # --------------------------------------------------
    # Verify persisted state.
    # --------------------------------------------------

    stage_run = await executor.run_service.get_stage(
        db_session,
        run.id,
        StageName.INGEST,
    )

    assert stage_run is not None
    assert stage_run.attempt == MAX_STAGE_ATTEMPTS
    assert stage_run.status == StageStatus.FAILED

    saved_run = await executor.run_service.get_run(
        db_session,
        run.id,
    )

    assert saved_run is not None
    assert saved_run.status == "failed"