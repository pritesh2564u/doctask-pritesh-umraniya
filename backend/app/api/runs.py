from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.run_service import RunService
from app.agent.stages import StageName, StageStatus
from app.db.session import get_db
from app.models.project import Project
from app.models.run import Run
from app.models.stage import StageRun
from app.agent.graph import build_graph
from app.agent.decisions import StageDecision
from app.agent.stage_handlers import StageHandler
from app.models.reconciliation import ReconciliationResult

router = APIRouter(
    prefix="/projects",
    tags=["runs"],
)

run_service = RunService()

workflow_graph = build_graph()

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

@router.get("/{project_id}/runs")
async def get_project_runs(
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

    # Fetch all runs for this project.
    result = await db.execute(
        select(Run)
        .where(Run.project_id == project_id)
        .order_by(Run.created_at.desc())
    )

    runs = result.scalars().all()

    return {
        "project_id": str(project_id),
        "runs": [
            {
                "run_id": str(run.id),
                "status": run.status,
                "current_stage": run.current_stage,
                "created_at": run.created_at,
            }
            for run in runs
        ],
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

    total_input_tokens = sum(
        stage.input_tokens or 0
        for stage in stages
    )

    total_output_tokens = sum(
        stage.output_tokens or 0
        for stage in stages
    )

    total_tokens = sum(
        stage.total_tokens or 0
        for stage in stages
    )

    total_cost_usd = sum(
        float(stage.estimated_cost_usd or 0)
        for stage in stages
    )

    return {
        "run_id": str(run.id),
        "project_id": str(run.project_id),
        "status": run.status,
        "current_stage": run.current_stage,
        "usage": {
            "input_tokens": total_input_tokens,
            "output_tokens": total_output_tokens,
            "total_tokens": total_tokens,
            "estimated_cost_usd": total_cost_usd,
        },
        "stages": [
            {
                "stage": stage.stage,
                "status": stage.status,
                "attempt": stage.attempt,
                "message": stage.message,
                "details": stage.details or {},
                "started_at": (
                    stage.started_at.isoformat()
                    if stage.started_at
                    else None
                ),
                "completed_at": (
                    stage.completed_at.isoformat()
                    if stage.completed_at
                    else None
                ),
                "duration_ms": stage.duration_ms,
                "input_tokens": stage.input_tokens or 0,
                "output_tokens": stage.output_tokens or 0,
                "total_tokens": stage.total_tokens or 0,
                "estimated_cost_usd": float(
                    stage.estimated_cost_usd or 0
                ),
                "error": stage.error,
            }
            for stage in stages
        ],
    }

@router.get("/{project_id}/runs/{run_id}/reconciliation")
async def get_reconciliation(
    project_id: UUID,
    run_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    # Verify run belongs to project.
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
        select(ReconciliationResult)
        .where(
            ReconciliationResult.run_id == run_id,
        )
        .order_by(ReconciliationResult.created_at)
    )

    conflicts = result.scalars().all()

    return {
        "run_id": str(run_id),
        "conflicts": [
            {
                "id": str(conflict.id),
                "conflict_type": conflict.conflict_type,
                "status": conflict.status,
                "description": conflict.description,
            }
            for conflict in conflicts
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

    # --------------------------------------------------
    # Execute the complete LangGraph workflow.
    #
    # The graph itself determines whether to continue
    # to another stage or stop at escalation/failure.
    # --------------------------------------------------

    workflow_result = await workflow_graph.ainvoke(
        {
            "run_id": run_id,
            "project_id": project_id,
        }
    )

    return {
        "run_id": str(run_id),
        "decision": workflow_result["decision"],
        "message": workflow_result["message"],
        "data": workflow_result.get("data", {}),
    }

@router.post(
    "/{project_id}/runs/{run_id}/reconciliation/{reconciliation_id}/resolve"
)
async def resolve_reconciliation(
    project_id: UUID,
    run_id: UUID,
    reconciliation_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    # --------------------------------------------------
    # Verify run belongs to project.
    # --------------------------------------------------

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

    # --------------------------------------------------
    # Resolve the requested reconciliation conflict.
    # --------------------------------------------------

    handler = StageHandler()

    result = await handler.resolve_reconciliation(
        db=db,
        run_id=run_id,
        reconciliation_id=reconciliation_id,
    )

    if result.decision == StageDecision.FAIL:
        raise HTTPException(
            status_code=404,
            detail=result.message,
        )

    # --------------------------------------------------
    # Check whether any reconciliation conflicts remain.
    # --------------------------------------------------

    conflict_result = await db.execute(
        select(ReconciliationResult).where(
            ReconciliationResult.run_id == run_id,
            ReconciliationResult.status == "open",
        )
    )

    open_conflicts = conflict_result.scalars().all()

    # --------------------------------------------------
    # Other conflicts still need human resolution.
    # Do not resume the workflow yet.
    # --------------------------------------------------

    if open_conflicts:
        return {
            "run_id": str(run_id),
            "reconciliation_id": str(
                reconciliation_id
            ),
            "status": result.data["status"],
            "message": (
                "Reconciliation conflict resolved. "
                f"{len(open_conflicts)} conflict(s) still "
                "require resolution."
            ),
            "workflow_resumed": False,
            "remaining_conflicts": len(open_conflicts),
        }

    # --------------------------------------------------
    # ALL reconciliation conflicts are now resolved.
    #
    # Re-open REVIEW so the executor can execute it again.
    # --------------------------------------------------

    review_result = await db.execute(
        select(StageRun).where(
            StageRun.run_id == run_id,
            StageRun.stage == StageName.REVIEW,
        )
    )

    review_stage = review_result.scalar_one_or_none()

    if review_stage is None:
        raise HTTPException(
            status_code=500,
            detail="Review stage not found",
        )

    if review_stage.status == StageStatus.ESCALATED:
        review_stage.status = StageStatus.PENDING

    run.status = "running"

    await db.commit()

    # --------------------------------------------------
    # Resume the persisted workflow.
    # --------------------------------------------------

    try:
        workflow_result = await workflow_graph.ainvoke(
            {
                "run_id": run_id,
                "project_id": project_id,
            }
        )

    except Exception as exc:
        return {
            "run_id": str(run_id),
            "reconciliation_id": str(
                reconciliation_id
            ),
            "status": result.data["status"],
            "message": (
                "Reconciliation conflict resolved, "
                "but workflow resume failed."
            ),
            "workflow_resumed": False,
            "workflow_error": str(exc),
        }

    return {
        "run_id": str(run_id),
        "reconciliation_id": str(
            reconciliation_id
        ),
        "status": result.data["status"],
        "message": (
            "Reconciliation conflict resolved and "
            "workflow resumed."
        ),
        "workflow_resumed": True,
        "workflow_decision": workflow_result.get(
            "decision"
        ),
        "workflow_message": workflow_result.get(
            "message"
        ),
        "workflow_data": workflow_result.get(
            "data",
            {},
        ),
    }