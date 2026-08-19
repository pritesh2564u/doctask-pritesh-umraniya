from typing import TypedDict
from uuid import UUID


class AgentState(TypedDict, total=False):
    run_id: UUID
    project_id: UUID

    current_stage: str

    decision: str
    message: str

    data: dict

    error: str | None