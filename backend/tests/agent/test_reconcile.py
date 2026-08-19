import pytest
from uuid import uuid4

from sqlalchemy import select

from app.agent.decisions import StageDecision
from app.agent.stage_handlers import StageHandler
from app.models.chunk import DocumentChunk
from app.models.document import Document
from app.models.finding import Finding
from app.models.project import Project
from app.models.run import Run
from app.models.reconciliation import ReconciliationResult

@pytest.mark.asyncio
async def test_reconcile_isolated_by_run(
    db_session,
):
    # --------------------------------------------------
    # Create one project.
    # --------------------------------------------------

    project = Project(
        name=f"Reconcile Isolation {uuid4()}",
    )

    db_session.add(project)
    await db_session.flush()

    # --------------------------------------------------
    # Create one document for the project.
    # --------------------------------------------------

    document = Document(
        project_id=project.id,
        filename="reconcile-test.txt",
        storage_path="tests/reconcile-test.txt",
        content_hash=f"hash-{uuid4()}",
    )

    db_session.add(document)
    await db_session.flush()

    # --------------------------------------------------
    # Create real document chunks.
    # --------------------------------------------------

    chunk_a = DocumentChunk(
        document_id=document.id,
        chunk_index=0,
        text="Project A is completed successfully.",
    )

    chunk_b = DocumentChunk(
        document_id=document.id,
        chunk_index=1,
        text="Project B is still in progress.",
    )

    db_session.add_all([
        chunk_a,
        chunk_b,
    ])

    await db_session.flush()

    # --------------------------------------------------
    # Create two runs for the SAME project.
    # --------------------------------------------------

    run_a = Run(
        project_id=project.id,
        status="running",
        current_stage="reconcile",
    )

    run_b = Run(
        project_id=project.id,
        status="running",
        current_stage="reconcile",
    )

    db_session.add_all([
        run_a,
        run_b,
    ])

    await db_session.flush()

    # --------------------------------------------------
    # Create findings belonging to different runs.
    #
    # Use real chunk IDs so the FK constraint is valid.
    # --------------------------------------------------

    finding_a = Finding(
        run_id=run_a.id,
        chunk_id=chunk_a.id,
        title="Run A finding",
        description="Run A evidence",
        status="pending",
    )

    finding_b = Finding(
        run_id=run_b.id,
        chunk_id=chunk_b.id,
        title="Run B finding",
        description="Run B evidence",
        status="pending",
    )

    db_session.add_all([
        finding_a,
        finding_b,
    ])

    await db_session.commit()

    # --------------------------------------------------
    # Run reconciliation for Run A.
    # --------------------------------------------------

    handler = StageHandler()

    result = await handler.reconcile(
        db=db_session,
        project_id=project.id,
        run_id=run_a.id,
    )

    # --------------------------------------------------
    # Reconciliation should complete.
    # --------------------------------------------------

    assert result.decision == StageDecision.COMPLETE

    # --------------------------------------------------
    # Verify findings are still isolated.
    #
    # Reconciliation for Run A must not modify Run B.
    # --------------------------------------------------

    result = await db_session.execute(
        select(Finding).where(
            Finding.run_id == run_a.id,
        )
    )

    run_a_findings = result.scalars().all()

    result = await db_session.execute(
        select(Finding).where(
            Finding.run_id == run_b.id,
        )
    )

    run_b_findings = result.scalars().all()

    assert len(run_a_findings) == 1
    assert len(run_b_findings) == 1

    assert run_a_findings[0].run_id == run_a.id
    assert run_b_findings[0].run_id == run_b.id

    assert run_a_findings[0].title == "Run A finding"
    assert run_b_findings[0].title == "Run B finding"

@pytest.mark.asyncio
async def test_reconcile_detects_conflicting_statuses(
    db_session,
):
    project = Project(
        name=f"Conflict Test {uuid4()}",
    )

    db_session.add(project)
    await db_session.flush()

    document = Document(
        project_id=project.id,
        filename="conflict-test.txt",
        storage_path="tests/conflict-test.txt",
        content_hash=f"hash-{uuid4()}",
    )

    db_session.add(document)
    await db_session.flush()

    completed_chunk = DocumentChunk(
        document_id=document.id,
        chunk_index=0,
        text="The project has been completed.",
    )

    progress_chunk = DocumentChunk(
        document_id=document.id,
        chunk_index=1,
        text="The project is still in progress.",
    )

    db_session.add_all([
        completed_chunk,
        progress_chunk,
    ])

    await db_session.flush()

    run = Run(
        project_id=project.id,
        status="running",
        current_stage="reconcile",
    )

    db_session.add(run)
    await db_session.commit()

    handler = StageHandler()

    result = await handler.reconcile(
        db=db_session,
        project_id=project.id,
        run_id=run.id,
    )

    assert result.decision == StageDecision.COMPLETE
    assert result.data["conflict_count"] == 1

    conflict = result.data["conflicts"][0]

    assert set(conflict["statuses"]) == {
        "completed",
        "in_progress",
    }

    assert set(conflict["chunk_ids"]) == {
        str(completed_chunk.id),
        str(progress_chunk.id),
    }

@pytest.mark.asyncio
async def test_reconcile_persistence_is_idempotent(
    db_session,
):
    project = Project(
        name=f"Reconcile Idempotency {uuid4()}",
    )

    db_session.add(project)
    await db_session.flush()

    document = Document(
        project_id=project.id,
        filename="idempotency-test.txt",
        storage_path="tests/idempotency-test.txt",
        content_hash=f"hash-{uuid4()}",
    )

    db_session.add(document)
    await db_session.flush()

    completed_chunk = DocumentChunk(
        document_id=document.id,
        chunk_index=0,
        text="The project has been completed.",
    )

    progress_chunk = DocumentChunk(
        document_id=document.id,
        chunk_index=1,
        text="The project is still in progress.",
    )

    db_session.add_all([
        completed_chunk,
        progress_chunk,
    ])

    await db_session.flush()

    run = Run(
        project_id=project.id,
        status="running",
        current_stage="reconcile",
    )

    db_session.add(run)
    await db_session.commit()

    handler = StageHandler()

    # First reconciliation.
    first_result = await handler.reconcile(
        db=db_session,
        project_id=project.id,
        run_id=run.id,
    )

    assert first_result.decision == StageDecision.COMPLETE
    assert first_result.data["conflict_count"] == 1

    result = await db_session.execute(
        select(ReconciliationResult).where(
            ReconciliationResult.run_id == run.id
        )
    )

    first_records = result.scalars().all()

    assert len(first_records) == 1
    assert first_records[0].status == "open"

    # Second reconciliation of the same run.
    second_result = await handler.reconcile(
        db=db_session,
        project_id=project.id,
        run_id=run.id,
    )

    assert second_result.decision == StageDecision.COMPLETE
    assert second_result.data["conflict_count"] == 1

    result = await db_session.execute(
        select(ReconciliationResult).where(
            ReconciliationResult.run_id == run.id
        )
    )

    second_records = result.scalars().all()

    # No duplicate reconciliation result.
    assert len(second_records) == 1
    assert second_records[0].id == first_records[0].id

@pytest.mark.asyncio
async def test_reconciliation_conflict_can_be_resolved(
    db_session,
):
    project = Project(
        name=f"Reconcile Resolution {uuid4()}",
    )

    db_session.add(project)
    await db_session.flush()

    run = Run(
        project_id=project.id,
        status="running",
        current_stage="reconcile",
    )

    db_session.add(run)
    await db_session.commit()

    reconciliation = ReconciliationResult(
        run_id=run.id,
        conflict_type="status_conflict",
        description="Project status is contradictory.",
        status="open",
    )

    db_session.add(reconciliation)
    await db_session.commit()

    reconciliation_id = reconciliation.id

    handler = StageHandler()

    result = await handler.resolve_reconciliation(
        db=db_session,
        run_id=run.id,
        reconciliation_id=reconciliation_id,
    )

    assert result.decision == StageDecision.COMPLETE

    saved = await db_session.get(
        ReconciliationResult,
        reconciliation_id,
    )

    assert saved is not None
    assert saved.status == "resolved"