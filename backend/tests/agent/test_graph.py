import pytest

from app.agent.graph import build_graph


@pytest.mark.asyncio
async def test_graph_can_start():

    graph = build_graph()

    assert graph is not None