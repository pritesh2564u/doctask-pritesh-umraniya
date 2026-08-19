from uuid import UUID

from app.agent.executor import WorkflowExecutor
from app.agent.state import AgentState
from app.db.session import AsyncSessionLocal


async def execute_stage(
    state: AgentState,
) -> AgentState:

    run_id: UUID = state["run_id"]

    async with AsyncSessionLocal() as db:

        executor = WorkflowExecutor()

        result = await executor.execute_next(
            db=db,
            run_id=run_id,
        )

        return {
            **state,
            "decision": result.decision.value,
            "message": result.message,
            "data": result.data or {},
        }