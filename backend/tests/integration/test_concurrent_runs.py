import asyncio
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.agent.run_service import RunService
from app.agent.stages import STAGE_ORDER, StageStatus
from app.core.config import settings
from app.models.project import Project
from app.models.run import Run
from app.models.stage import StageRun


@pytest.mark.asyncio
async def test_two_runs_can_be_created_concurrently(
    db_session: AsyncSession,
):
    # --------------------------------------------------
    # Create one project using the test session.
    # --------------------------------------------------

    project = Project(
        name=f"Concurrent Runs {uuid4()}",
    )

    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    service = RunService()

    # --------------------------------------------------
    # Create a separate engine for the concurrent tasks.
    #
    # IMPORTANT:
    # Do NOT use app.db.session.AsyncSessionLocal here.
    # That is the application's global connection pool.
    # --------------------------------------------------

    test_engine = create_async_engine(
        settings.database_url,
        pool_pre_ping=True,
    )

    TestSessionLocal = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def create_run():
        async with TestSessionLocal() as session:
            return await service.create_run(
                session,
                project.id,
            )

    try:
        # --------------------------------------------------
        # Create Run A and Run B concurrently.
        # --------------------------------------------------

        run_a, run_b = await asyncio.gather(
            create_run(),
            create_run(),
        )

        # --------------------------------------------------
        # They must have different IDs.
        # --------------------------------------------------

        assert run_a.id != run_b.id

        # Both belong to the same project.
        assert run_a.project_id == project.id
        assert run_b.project_id == project.id

        # --------------------------------------------------
        # Verify database state using the test session.
        # --------------------------------------------------

        result = await db_session.execute(
            select(Run).where(
                Run.project_id == project.id
            )
        )

        runs = result.scalars().all()

        run_ids = {
            run.id
            for run in runs
        }

        assert run_a.id in run_ids
        assert run_b.id in run_ids

        # --------------------------------------------------
        # Verify StageRun records.
        # --------------------------------------------------

        result = await db_session.execute(
            select(StageRun).where(
                StageRun.run_id.in_(
                    [
                        run_a.id,
                        run_b.id,
                    ]
                )
            )
        )

        stage_runs = result.scalars().all()

        stages_by_run = {
            run_a.id: [],
            run_b.id: [],
        }

        for stage_run in stage_runs:
            stages_by_run[
                stage_run.run_id
            ].append(stage_run)

        # Each run must have every stage.
        assert len(
            stages_by_run[run_a.id]
        ) == len(STAGE_ORDER)

        assert len(
            stages_by_run[run_b.id]
        ) == len(STAGE_ORDER)

        # --------------------------------------------------
        # Verify Run A stages.
        # --------------------------------------------------

        for stage_run in stages_by_run[run_a.id]:
            assert stage_run.run_id == run_a.id
            assert stage_run.status == StageStatus.PENDING

        # --------------------------------------------------
        # Verify Run B stages.
        # --------------------------------------------------

        for stage_run in stages_by_run[run_b.id]:
            assert stage_run.run_id == run_b.id
            assert stage_run.status == StageStatus.PENDING

    finally:
        # --------------------------------------------------
        # Very important:
        # Dispose the concurrent test engine while the
        # current event loop is still alive.
        # --------------------------------------------------

        await test_engine.dispose()