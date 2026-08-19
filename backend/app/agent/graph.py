from langgraph.graph import END, START, StateGraph

from app.agent.nodes import execute_stage
from app.agent.state import AgentState


def route_after_stage(
    state: AgentState,
):
    decision = state.get("decision")

    if decision == "escalate":
        return END

    if decision == "fail":
        return END

    if decision == "retry":
        return "execute_stage"

    if decision in {
        "complete",
        "skip",
    }:
        return "execute_stage"

    return END


def build_graph():

    graph = StateGraph(AgentState)

    graph.add_node(
        "execute_stage",
        execute_stage,
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