import asyncio
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.agent.stage_handlers import StageHandler
from app.db.session import AsyncSessionLocal
from app.models.chunk import DocumentChunk
from app.models.document import Document
from app.models.finding import Finding
from app.models.project import Project
from app.models.run import Run


@pytest.mark.asyncio
async def test_two_runs_analyze_concurrently_are_isolated(db_session):
    # --------------------------------------------------
    # Create project
    # --------------------------------------------------

    project = Project(
        name=f"Concurrent Analyze {uuid4()}",
    )

    db_session.add(project)
    await db_session.flush()

    # --------------------------------------------------
    # Create document
    # --------------------------------------------------

    document = Document(
        project_id=project.id,
        filename="concurrent-analyze.txt",
        storage_path="tests/concurrent-analyze.txt",
        content_hash=f"hash-{uuid4()}",
    )

    db_session.add(document)
    await db_session.flush()

    # --------------------------------------------------
    # Create chunks containing risk keywords
    # --------------------------------------------------

    chunk_a = DocumentChunk(
        document_id=document.id,
        chunk_index=0,
        text="Project A has a critical delivery risk.",
    )

    chunk_b = DocumentChunk(
        document_id=document.id,
        chunk_index=1,
        text="Project B has a delayed delivery issue.",
    )

    db_session.add_all([
        chunk_a,
        chunk_b,
    ])

    await db_session.flush()

    # --------------------------------------------------
    # Create two runs for the SAME project
    # --------------------------------------------------

    run_a = Run(
        project_id=project.id,
        status="running",
        current_stage="analyze",
    )

    run_b = Run(
        project_id=project.id,
        status="running",
        current_stage="analyze",
    )

    db_session.add_all([
        run_a,
        run_b,
    ])

    await db_session.commit()

    # --------------------------------------------------
    # Execute ANALYZE concurrently.
    #
    # Each concurrent execution gets its own DB session.
    # --------------------------------------------------

    async def analyze_run(run_id):
        async with AsyncSessionLocal() as session:
            handler = StageHandler()

            return await handler.analyze(
                db=session,
                project_id=project.id,
                run_id=run_id,
            )

    result_a, result_b = await asyncio.gather(
        analyze_run(run_a.id),
        analyze_run(run_b.id),
    )

    # Both analyses should complete.
    assert result_a.decision.value == "complete"
    assert result_b.decision.value == "complete"

    # --------------------------------------------------
    # Verify Run A findings
    # --------------------------------------------------

    result = await db_session.execute(
        select(Finding).where(
            Finding.run_id == run_a.id
        )
    )

    findings_a = result.scalars().all()

    # --------------------------------------------------
    # Verify Run B findings
    # --------------------------------------------------

    result = await db_session.execute(
        select(Finding).where(
            Finding.run_id == run_b.id
        )
    )

    findings_b = result.scalars().all()

    # --------------------------------------------------
    # Each run should have its own findings.
    # --------------------------------------------------

    assert len(findings_a) == 2
    assert len(findings_b) == 2

    assert all(
        finding.run_id == run_a.id
        for finding in findings_a
    )

    assert all(
        finding.run_id == run_b.id
        for finding in findings_b
    )

    chunk_ids_a = {
        finding.chunk_id
        for finding in findings_a
    }

    chunk_ids_b = {
        finding.chunk_id
        for finding in findings_b
    }

    # Same project → same source chunks.
    assert chunk_ids_a == chunk_ids_b

    # Different runs → different finding ownership.
    assert all(
        finding.run_id != run_b.id
        for finding in findings_a
    )

    assert all(
        finding.run_id != run_a.id
        for finding in findings_b
    )