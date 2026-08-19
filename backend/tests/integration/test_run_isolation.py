from uuid import uuid4

import pytest
from sqlalchemy import select

from app.models.document import Document
from app.models.chunk import DocumentChunk
from app.models.finding import Finding
from app.models.project import Project
from app.models.run import Run


@pytest.mark.asyncio
async def test_two_runs_same_project_are_isolated(db_session):
    # --------------------------------------------------
    # 1. Create one project
    # --------------------------------------------------

    project = Project(
        name=f"Concurrency Test {uuid4()}",
    )

    db_session.add(project)
    await db_session.flush()

    # --------------------------------------------------
    # 2. Create a document belonging to the project
    # --------------------------------------------------

    document = Document(
        project_id=project.id,
        filename="concurrency-test.txt",
        storage_path="tests/concurrency-test.txt",
        content_hash="test-content-hash-concurrency",
    )

    db_session.add(document)
    await db_session.flush()

    # --------------------------------------------------
    # 3. Create TWO real document chunks
    # --------------------------------------------------

    chunk_a = DocumentChunk(
        document_id=document.id,
        chunk_index=0,
        text="Content belonging to finding A",
    )

    chunk_b = DocumentChunk(
        document_id=document.id,
        chunk_index=1,
        text="Content belonging to finding B",
    )

    db_session.add_all([
        chunk_a,
        chunk_b,
    ])

    await db_session.flush()

    # --------------------------------------------------
    # 4. Create TWO runs for the SAME project
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

    await db_session.flush()

    # --------------------------------------------------
    # 5. Create findings belonging to different runs
    # --------------------------------------------------

    finding_a = Finding(
        run_id=run_a.id,
        chunk_id=chunk_a.id,
        title="Finding A",
        description="Belongs to run A",
        status="pending",
    )

    finding_b = Finding(
        run_id=run_b.id,
        chunk_id=chunk_b.id,
        title="Finding B",
        description="Belongs to run B",
        status="pending",
    )

    db_session.add_all([
        finding_a,
        finding_b,
    ])

    await db_session.commit()

    # --------------------------------------------------
    # 6. Query Run A
    # --------------------------------------------------

    result_a = await db_session.execute(
        select(Finding).where(
            Finding.run_id == run_a.id
        )
    )

    findings_a = result_a.scalars().all()

    # --------------------------------------------------
    # 7. Query Run B
    # --------------------------------------------------

    result_b = await db_session.execute(
        select(Finding).where(
            Finding.run_id == run_b.id
        )
    )

    findings_b = result_b.scalars().all()

    # --------------------------------------------------
    # 8. Verify isolation
    # --------------------------------------------------

    assert len(findings_a) == 1
    assert findings_a[0].title == "Finding A"
    assert findings_a[0].run_id == run_a.id

    assert len(findings_b) == 1
    assert findings_b[0].title == "Finding B"
    assert findings_b[0].run_id == run_b.id

    # Most important assertion:
    assert findings_a[0].run_id != findings_b[0].run_id

    # Each run must not see the other's finding.
    assert all(
        finding.run_id == run_a.id
        for finding in findings_a
    )

    assert all(
        finding.run_id == run_b.id
        for finding in findings_b
    )