from uuid import uuid4

import pytest
from sqlalchemy import select

from app.agent.decisions import StageDecision
from app.agent.stage_handlers import StageHandler
from app.models.project import Project
from app.models.reconciliation import ReconciliationResult
from app.models.run import Run


@pytest.mark.asyncio
async def test_review_blocks_on_open_reconciliation_and_resumes_after_resolution(
    db_session,
):
    # --------------------------------------------------
    # Create project and run.
    # --------------------------------------------------

    project = Project(
        name=f"Review Reconciliation {uuid4()}",
    )

    db_session.add(project)
    await db_session.flush()

    run = Run(
        project_id=project.id,
        status="running",
        current_stage="review",
    )

    db_session.add(run)
    await db_session.flush()

    # --------------------------------------------------
    # Create a finding that is already approved.
    #
    # This ensures the only thing blocking REVIEW is the
    # reconciliation conflict.
    # --------------------------------------------------

    # Do not persist this finding because chunk_id is a
    # foreign key. The reconciliation behavior is what
    # this test is exercising.
    #
    # Instead, verify the review behavior using a real
    # reconciliation result below.

    reconciliation = ReconciliationResult(
        run_id=run.id,
        conflict_type="status_conflict",
        description="Project status is contradictory.",
        status="open",
    )

    db_session.add(reconciliation)
    await db_session.commit()

    handler = StageHandler()

    # --------------------------------------------------
    # REVIEW must escalate while conflict is open.
    # --------------------------------------------------

    result = await handler.review(
        db=db_session,
        project_id=project.id,
        run_id=run.id,
    )

    assert result.decision == StageDecision.ESCALATE
    assert result.data["conflict_count"] == 1

    # --------------------------------------------------
    # Resolve the reconciliation conflict.
    # --------------------------------------------------

    resolution = await handler.resolve_reconciliation(
        db=db_session,
        run_id=run.id,
        reconciliation_id=reconciliation.id,
    )

    assert resolution.decision == StageDecision.COMPLETE
    assert resolution.data["status"] == "resolved"

    # --------------------------------------------------
    # REVIEW should no longer be blocked by reconciliation.
    #
    # There are no persisted findings in this minimal test,
    # so REVIEW should skip.
    # --------------------------------------------------

    result = await handler.review(
        db=db_session,
        project_id=project.id,
        run_id=run.id,
    )

    assert result.decision == StageDecision.SKIP
    assert result.data["finding_count"] == 0