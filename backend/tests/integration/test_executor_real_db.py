import pytest

from app.agent.executor import WorkflowExecutor
from app.agent.run_service import RunService
from app.db.session import AsyncSessionLocal
from app.models.project import Project


@pytest.mark.asyncio
async def test_executor_can_load_real_run():
    async with AsyncSessionLocal() as db:
        project = Project(
            name="Executor DB Test",
        )

        db.add(project)
        await db.flush()

        run_service = RunService()

        run = await run_service.create_run(
            db=db,
            project_id=project.id,
        )

        await db.commit()

    async with AsyncSessionLocal() as db:
        executor = WorkflowExecutor()

        result = await executor.run_service.get_run(
            db=db,
            run_id=run.id,
        )

        assert result is not None
        assert result.id == run.id