from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.run_service import RunService
from app.agent.stages import StageName
from app.db.session import get_db
from app.models.project import Project
from app.models.run import Run
from app.models.stage import StageRun
from app.agent.decisions import StageDecision
from app.agent.executor import StageResult, WorkflowExecutor
from app.agent.stages import StageName

router = APIRouter(
    prefix="/projects",
    tags=["runs"],
)

run_service = RunService()

workflow_executor = WorkflowExecutor()

@router.post("/{project_id}/runs")
async def create_run(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    # Verify project exists.
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )

    project = result.scalar_one_or_none()

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    run = await run_service.create_run(
        db=db,
        project_id=project_id,
    )

    return {
        "run_id": str(run.id),
        "project_id": str(run.project_id),
        "status": run.status,
        "current_stage": run.current_stage,
    }


@router.get("/{project_id}/runs/{run_id}")
async def get_run_status(
    project_id: UUID,
    run_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Run).where(
            Run.id == run_id,
            Run.project_id == project_id,
        )
    )

    run = result.scalar_one_or_none()

    if run is None:
        raise HTTPException(
            status_code=404,
            detail="Run not found",
        )

    result = await db.execute(
        select(StageRun)
        .where(StageRun.run_id == run_id)
    )

    stages = result.scalars().all()

    stage_order = {
        "ingest": 0,
        "extract": 1,
        "analyze": 2,
        "reconcile": 3,
        "review": 4,
        "commit": 5,
    }

    stages.sort(
        key=lambda stage: stage_order.get(
            str(stage.stage),
            999,
        )
    )

    return {
        "run_id": str(run.id),
        "project_id": str(run.project_id),
        "status": run.status,
        "current_stage": run.current_stage,
        "stages": [
            {
                "stage": stage.stage,
                "status": stage.status,
                "attempt": stage.attempt,
            }
            for stage in stages
        ],
    }

@router.post("/{project_id}/runs/{run_id}/execute")
async def execute_run(
    project_id: UUID,
    run_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Run).where(
            Run.id == run_id,
            Run.project_id == project_id,
        )
    )

    run = result.scalar_one_or_none()

    if run is None:
        raise HTTPException(
            status_code=404,
            detail="Run not found",
        )

    workflow_result = await workflow_executor.execute_next(
        db=db,
        run_id=run_id,
    )

    return {
        "run_id": str(run_id),
        "decision": workflow_result.decision,
        "message": workflow_result.message,
        "data": workflow_result.data,
    }