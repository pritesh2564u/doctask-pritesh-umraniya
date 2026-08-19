import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.agent.graph import build_graph
from app.agent.run_service import RunService
from app.core.config import settings
from app.models.chunk import DocumentChunk
from app.models.document import Document
from app.models.project import Project
from app.models.run import Run
from app.models.stage import StageRun


@pytest.mark.asyncio
async def test_real_workflow_persists_stage_progression():
    # --------------------------------------------------
    # Create a test-local engine.
    #
    # NullPool is intentional for integration tests:
    # every session gets a fresh DB connection, avoiding
    # async connection-pool/event-loop reuse issues.
    # --------------------------------------------------

    test_engine = create_async_engine(
        settings.database_url,
        poolclass=NullPool,
    )

    TestSessionLocal = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    try:
        # --------------------------------------------------
        # Create persisted test data.
        # --------------------------------------------------

        async with TestSessionLocal() as db:
            project = Project(
                name="Real Workflow Integration Test",
            )

            db.add(project)
            await db.flush()

            project_id = project.id

            # --------------------------------------------------
            # Create document.
            # --------------------------------------------------

            document = Document(
                project_id=project_id,
                filename="workflow-test.txt",
                storage_path="tests/workflow-test.txt",
                content_hash="workflow-test-hash",
            )

            db.add(document)
            await db.flush()

            # --------------------------------------------------
            # Create evidence chunk.
            #
            # This prevents INGEST from retrying because the
            # project contains document evidence.
            # --------------------------------------------------

            chunk = DocumentChunk(
                document_id=document.id,
                chunk_index=0,
                text=(
                    "Project Alpha was completed successfully. "
                    "All planned milestones were completed."
                ),
            )

            db.add(chunk)
            await db.flush()

            # --------------------------------------------------
            # Create run and its StageRun records.
            # --------------------------------------------------

            run_service = RunService()

            run = await run_service.create_run(
                db=db,
                project_id=project_id,
            )

            run_id = run.id

            # --------------------------------------------------
            # Commit setup data before LangGraph starts.
            # --------------------------------------------------

            await db.commit()

        # --------------------------------------------------
        # Build the REAL LangGraph.
        #
        # Pass the test session factory so the graph uses the
        # same test-local DB infrastructure.
        # --------------------------------------------------

        graph = build_graph(
            session_factory=TestSessionLocal,
        )

        # --------------------------------------------------
        # Execute the actual persisted workflow.
        # --------------------------------------------------

        result = await graph.ainvoke(
            {
                "run_id": run_id,
                "project_id": project_id,
            },
            config={
                "recursion_limit": 20,
            },
        )

        # --------------------------------------------------
        # Graph must return a valid decision.
        # --------------------------------------------------

        assert result["decision"] in {
            "complete",
            "retry",
            "skip",
            "escalate",
            "fail",
        }

        assert "message" in result

        # --------------------------------------------------
        # Verify persisted workflow state.
        # --------------------------------------------------

        async with TestSessionLocal() as db:
            saved_run = await db.get(
                Run,
                run_id,
            )

            assert saved_run is not None
            assert saved_run.project_id == project_id

            # --------------------------------------------------
            # Load all persisted stages.
            # --------------------------------------------------

            stage_result = await db.execute(
                select(StageRun)
                .where(
                    StageRun.run_id == run_id
                )
            )

            stage_runs = stage_result.scalars().all()

            assert len(stage_runs) == 6

            stages = {
                str(stage.stage): stage
                for stage in stage_runs
            }

            # --------------------------------------------------
            # Every StageRun must belong to this run.
            # --------------------------------------------------

            assert all(
                stage.run_id == run_id
                for stage in stage_runs
            )

            # --------------------------------------------------
            # INGEST must have executed.
            # --------------------------------------------------

            assert stages["ingest"].attempt >= 1

            # --------------------------------------------------
            # EXTRACT must execute if INGEST completed.
            # --------------------------------------------------

            if stages["ingest"].status == "completed":
                assert stages["extract"].attempt >= 1

            # --------------------------------------------------
            # ANALYZE must execute if EXTRACT completed.
            # --------------------------------------------------

            if stages["extract"].status == "completed":
                assert stages["analyze"].attempt >= 1

            # --------------------------------------------------
            # RECONCILE must execute if ANALYZE completed.
            # --------------------------------------------------

            if stages["analyze"].status == "completed":
                assert stages["reconcile"].attempt >= 1

            # --------------------------------------------------
            # REVIEW must execute if RECONCILE completed.
            # --------------------------------------------------

            if stages["reconcile"].status == "completed":
                assert stages["review"].attempt >= 1

            # --------------------------------------------------
            # COMMIT must execute only when REVIEW completes.
            # --------------------------------------------------

            if stages["review"].status == "completed":
                assert stages["commit"].attempt >= 1

    finally:
        # --------------------------------------------------
        # Always dispose the test engine.
        # --------------------------------------------------

        await test_engine.dispose()