from uuid import UUID

from app.agent.factory import create_workflow_executor
from app.agent.state import AgentState
from app.db.session import AsyncSessionLocal


async def execute_stage(
    state: AgentState,
    session_factory=AsyncSessionLocal,
) -> AgentState:

    run_id: UUID = state["run_id"]

    async with session_factory() as db:

        executor = create_workflow_executor()

        result = await executor.execute_next(
            db=db,
            run_id=run_id,
        )

        data = result.data or {}

        return {
            **state,
            "decision": result.decision.value,
            "message": result.message,
            "data": data,
            "workflow_complete": data.get(
                "workflow_complete",
                False,
            ),
        }