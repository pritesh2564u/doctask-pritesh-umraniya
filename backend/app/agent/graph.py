from langgraph.graph import END, START, StateGraph

from app.agent.nodes import execute_stage
from app.agent.state import AgentState


def route_after_stage(state: AgentState):
    if state.get("workflow_complete") is True:
        return END

    decision = state.get("decision")

    if decision in {
        "complete",
        "skip",
        "retry",
    }:
        return "execute_stage"

    return END


def build_graph(session_factory=None):

    if session_factory is None:
        from app.db.session import AsyncSessionLocal

        session_factory = AsyncSessionLocal

    async def execute_stage_node(
        state: AgentState,
    ):
        return await execute_stage(
            state,
            session_factory=session_factory,
        )

    graph = StateGraph(AgentState)

    graph.add_node(
        "execute_stage",
        execute_stage_node,
    )

    graph.add_edge(
        START,
        "execute_stage",
    )

    graph.add_conditional_edges(
        "execute_stage",
        route_after_stage,
    )

    return graph.compile()