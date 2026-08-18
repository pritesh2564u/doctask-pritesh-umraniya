from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.stages import (
    STAGE_ORDER,
    StageName,
    StageStatus,
)
from app.models.run import Run
from app.models.stage import StageRun


class RunService:

    async def create_run(
        self,
        db: AsyncSession,
        project_id: UUID,
    ) -> Run:
        run = Run(
            project_id=project_id,
            status="running",
            current_stage=StageName.INGEST,
        )

        db.add(run)
        await db.flush()

        for stage in STAGE_ORDER:
            db.add(
                StageRun(
                    run_id=run.id,
                    stage=stage,
                    status=StageStatus.PENDING,
                    attempt=0,
                )
            )

        await db.commit()
        await db.refresh(run)

        return run

    async def get_run(
        self,
        db: AsyncSession,
        run_id: UUID,
    ) -> Run | None:
        result = await db.execute(
            select(Run).where(Run.id == run_id)
        )

        return result.scalar_one_or_none()

    async def get_stage(
        self,
        db: AsyncSession,
        run_id: UUID,
        stage: StageName,
    ) -> StageRun | None:
        result = await db.execute(
            select(StageRun).where(
                StageRun.run_id == run_id,
                StageRun.stage == stage,
            )
        )

        return result.scalar_one_or_none()

    async def start_stage(
        self,
        db: AsyncSession,
        run_id: UUID,
        stage: StageName,
    ) -> StageRun:
        stage_run = await self.get_stage(
            db,
            run_id,
            stage,
        )

        if stage_run is None:
            raise ValueError(
                f"Stage {stage} does not exist"
            )

        stage_run.status = StageStatus.RUNNING
        stage_run.attempt += 1

        run = await self.get_run(db, run_id)

        if run is not None:
            run.current_stage = stage
            run.status = "running"

        await db.commit()
        await db.refresh(stage_run)

        return stage_run

    async def complete_stage(
        self,
        db: AsyncSession,
        run_id: UUID,
        stage: StageName,
    ) -> StageRun:
        stage_run = await self.get_stage(
            db,
            run_id,
            stage,
        )

        if stage_run is None:
            raise ValueError(
                f"Stage {stage} does not exist"
            )

        stage_run.status = StageStatus.COMPLETED

        await db.commit()
        await db.refresh(stage_run)

        return stage_run