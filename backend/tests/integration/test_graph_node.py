import pytest

from app.agent.nodes import execute_stage
from app.agent.run_service import RunService
from app.db.session import AsyncSessionLocal
from app.models.project import Project


@pytest.mark.asyncio
async def test_execute_stage_node_with_real_database():
    # --------------------------------------------------
    # Create real persisted run.
    # --------------------------------------------------

    async with AsyncSessionLocal() as db:
        project = Project(
            name="Graph Node DB Test",
        )

        db.add(project)
        await db.flush()

        run_service = RunService()

        run = await run_service.create_run(
            db=db,
            project_id=project.id,
        )

        await db.commit()

        run_id = run.id
        project_id = project.id

    # --------------------------------------------------
    # Execute the REAL LangGraph node directly.
    # --------------------------------------------------

    result = await execute_stage(
        {
            "run_id": run_id,
            "project_id": project_id,
        }
    )

    # --------------------------------------------------
    # Validate node output.
    # --------------------------------------------------

    assert result["run_id"] == run_id
    assert result["project_id"] == project_id

    assert result["decision"] in {
        "complete",
        "retry",
        "skip",
        "escalate",
        "fail",
    }

    assert "message" in result