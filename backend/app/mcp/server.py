from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from mcp.server.fastmcp import FastMCP
from sqlalchemy import select

from app.agent.graph import build_graph
from app.agent.run_service import RunService
from app.agent.stage_handlers import StageHandler
from app.agent.decisions import StageDecision
from app.agent.stages import StageName, StageStatus
from app.db.session import AsyncSessionLocal
from app.models.project import Project
from app.models.reconciliation import ReconciliationResult
from app.models.run import Run
from app.models.stage import StageRun


mcp = FastMCP("DocTask")

run_service = RunService()
workflow_graph = build_graph()
stage_handler = StageHandler()


def json_response(data: Any) -> str:
    return json.dumps(
        data,
        default=str,
        indent=2,
    )


async def get_project(
    db,
    project_id: UUID,
) -> Project | None:
    result = await db.execute(
        select(Project).where(
            Project.id == project_id
        )
    )

    return result.scalar_one_or_none()


async def get_project_run(
    db,
    project_id: UUID,
    run_id: UUID,
) -> Run | None:
    result = await db.execute(
        select(Run).where(
            Run.id == run_id,
            Run.project_id == project_id,
        )
    )

    return result.scalar_one_or_none()


@mcp.tool()
async def create_run(
    project_id: str,
) -> str:
    """
    Create a new persisted DocTask workflow run.

    The run starts at the ingest stage and is associated
    with the supplied project.
    """

    try:
        project_uuid = UUID(project_id)
    except ValueError:
        return json_response(
            {
                "success": False,
                "error": "Invalid project_id.",
            }
        )

    async with AsyncSessionLocal() as db:
        project = await get_project(
            db,
            project_uuid,
        )

        if project is None:
            return json_response(
                {
                    "success": False,
                    "error": "Project not found.",
                }
            )

        run = await run_service.create_run(
            db=db,
            project_id=project_uuid,
        )

        return json_response(
            {
                "success": True,
                "run_id": str(run.id),
                "project_id": str(run.project_id),
                "status": run.status,
                "current_stage": run.current_stage,
            }
        )


@mcp.tool()
async def get_run_status(
    project_id: str,
    run_id: str,
) -> str:
    """
    Get the complete persisted state of a workflow run,
    including every stage's status, attempt, timestamps,
    details, and errors.
    """

    try:
        project_uuid = UUID(project_id)
        run_uuid = UUID(run_id)
    except ValueError:
        return json_response(
            {
                "success": False,
                "error": "Invalid project_id or run_id.",
            }
        )

    async with AsyncSessionLocal() as db:
        run = await get_project_run(
            db,
            project_uuid,
            run_uuid,
        )

        if run is None:
            return json_response(
                {
                    "success": False,
                    "error": "Run not found.",
                }
            )

        result = await db.execute(
            select(StageRun).where(
                StageRun.run_id == run_uuid
            )
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

        return json_response(
            {
                "success": True,
                "run_id": str(run.id),
                "project_id": str(run.project_id),
                "status": run.status,
                "current_stage": run.current_stage,
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
                        "error": stage.error,
                    }
                    for stage in stages
                ],
            }
        )


@mcp.tool()
async def execute_run(
    project_id: str,
    run_id: str,
) -> str:
    """
    Execute the LangGraph workflow for an existing run.

    The graph determines whether to continue to another
    stage or stop because human reconciliation is required.
    """

    try:
        project_uuid = UUID(project_id)
        run_uuid = UUID(run_id)
    except ValueError:
        return json_response(
            {
                "success": False,
                "error": "Invalid project_id or run_id.",
            }
        )

    async with AsyncSessionLocal() as db:
        run = await get_project_run(
            db,
            project_uuid,
            run_uuid,
        )

        if run is None:
            return json_response(
                {
                    "success": False,
                    "error": "Run not found.",
                }
            )

    try:
        workflow_result = await workflow_graph.ainvoke(
            {
                "run_id": run_uuid,
                "project_id": project_uuid,
            }
        )

    except Exception as exc:
        return json_response(
            {
                "success": False,
                "run_id": run_id,
                "error": str(exc),
            }
        )

    return json_response(
        {
            "success": True,
            "run_id": run_id,
            "decision": workflow_result.get(
                "decision"
            ),
            "message": workflow_result.get(
                "message"
            ),
            "data": workflow_result.get(
                "data",
                {},
            ),
        }
    )


@mcp.tool()
async def get_reconciliation(
    project_id: str,
    run_id: str,
) -> str:
    """
    Get reconciliation conflicts requiring human review.
    """

    try:
        project_uuid = UUID(project_id)
        run_uuid = UUID(run_id)
    except ValueError:
        return json_response(
            {
                "success": False,
                "error": "Invalid project_id or run_id.",
            }
        )

    async with AsyncSessionLocal() as db:
        run = await get_project_run(
            db,
            project_uuid,
            run_uuid,
        )

        if run is None:
            return json_response(
                {
                    "success": False,
                    "error": "Run not found.",
                }
            )

        result = await db.execute(
            select(ReconciliationResult)
            .where(
                ReconciliationResult.run_id == run_uuid
            )
            .order_by(
                ReconciliationResult.created_at
            )
        )

        conflicts = result.scalars().all()

        return json_response(
            {
                "success": True,
                "run_id": run_id,
                "conflicts": [
                    {
                        "id": str(conflict.id),
                        "conflict_type": (
                            conflict.conflict_type
                        ),
                        "status": conflict.status,
                        "description": (
                            conflict.description
                        ),
                    }
                    for conflict in conflicts
                ],
            }
        )


@mcp.tool()
async def resolve_reconciliation(
    project_id: str,
    run_id: str,
    reconciliation_id: str,
) -> str:
    """
    Resolve one reconciliation conflict.

    If additional conflicts remain open, the workflow
    remains paused.

    If all conflicts are resolved, the workflow is
    resumed automatically.
    """

    try:
        project_uuid = UUID(project_id)
        run_uuid = UUID(run_id)
        reconciliation_uuid = UUID(
            reconciliation_id
        )
    except ValueError:
        return json_response(
            {
                "success": False,
                "error": (
                    "Invalid project_id, run_id, "
                    "or reconciliation_id."
                ),
            }
        )

    async with AsyncSessionLocal() as db:
        run = await get_project_run(
            db,
            project_uuid,
            run_uuid,
        )

        if run is None:
            return json_response(
                {
                    "success": False,
                    "error": "Run not found.",
                }
            )

        result = await stage_handler.resolve_reconciliation(
            db=db,
            run_id=run_uuid,
            reconciliation_id=reconciliation_uuid,
        )

        if result.decision == StageDecision.FAIL:
            return json_response(
                {
                    "success": False,
                    "run_id": run_id,
                    "reconciliation_id": (
                        reconciliation_id
                    ),
                    "error": result.message,
                }
            )

        conflict_result = await db.execute(
            select(ReconciliationResult).where(
                ReconciliationResult.run_id == run_uuid,
                ReconciliationResult.status == "open",
            )
        )

        open_conflicts = (
            conflict_result.scalars().all()
        )

        if open_conflicts:
            return json_response(
                {
                    "success": True,
                    "run_id": run_id,
                    "reconciliation_id": (
                        reconciliation_id
                    ),
                    "status": result.data[
                        "status"
                    ],
                    "message": (
                        "Reconciliation conflict "
                        "resolved. "
                        f"{len(open_conflicts)} "
                        "conflict(s) still require "
                        "resolution."
                    ),
                    "workflow_resumed": False,
                    "remaining_conflicts": len(
                        open_conflicts
                    ),
                }
            )

        review_result = await db.execute(
            select(StageRun).where(
                StageRun.run_id == run_uuid,
                StageRun.stage == StageName.REVIEW,
            )
        )

        review_stage = (
            review_result.scalar_one_or_none()
        )

        if review_stage is None:
            return json_response(
                {
                    "success": False,
                    "run_id": run_id,
                    "error": (
                        "Review stage not found."
                    ),
                }
            )

        if (
            review_stage.status
            == StageStatus.ESCALATED
        ):
            review_stage.status = (
                StageStatus.PENDING
            )

        run.status = "running"

        await db.commit()

    try:
        workflow_result = (
            await workflow_graph.ainvoke(
                {
                    "run_id": run_uuid,
                    "project_id": project_uuid,
                }
            )
        )

    except Exception as exc:
        return json_response(
            {
                "success": False,
                "run_id": run_id,
                "reconciliation_id": (
                    reconciliation_id
                ),
                "message": (
                    "Conflict resolved, but "
                    "workflow resume failed."
                ),
                "workflow_resumed": False,
                "error": str(exc),
            }
        )

    return json_response(
        {
            "success": True,
            "run_id": run_id,
            "reconciliation_id": (
                reconciliation_id
            ),
            "status": result.data["status"],
            "message": (
                "Reconciliation conflict resolved "
                "and workflow resumed."
            ),
            "workflow_resumed": True,
            "workflow_decision": (
                workflow_result.get("decision")
            ),
            "workflow_message": (
                workflow_result.get("message")
            ),
            "workflow_data": (
                workflow_result.get(
                    "data",
                    {},
                )
            ),
        }
    )


@mcp.tool()
async def list_project_runs(
    project_id: str,
) -> str:
    """
    List all workflow runs belonging to a project.
    """

    try:
        project_uuid = UUID(project_id)
    except ValueError:
        return json_response(
            {
                "success": False,
                "error": "Invalid project_id.",
            }
        )

    async with AsyncSessionLocal() as db:
        project = await get_project(
            db,
            project_uuid,
        )

        if project is None:
            return json_response(
                {
                    "success": False,
                    "error": "Project not found.",
                }
            )

        result = await db.execute(
            select(Run)
            .where(
                Run.project_id == project_uuid
            )
            .order_by(
                Run.created_at.desc()
            )
        )

        runs = result.scalars().all()

        return json_response(
            {
                "success": True,
                "project_id": project_id,
                "runs": [
                    {
                        "run_id": str(run.id),
                        "status": run.status,
                        "current_stage": (
                            run.current_stage
                        ),
                        "created_at": run.created_at,
                    }
                    for run in runs
                ],
            }
        )


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
    )