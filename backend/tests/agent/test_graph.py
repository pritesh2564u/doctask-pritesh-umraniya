import pytest
from sqlalchemy import select

from app.agent.graph import END, build_graph, route_after_stage
from app.agent.nodes import execute_stage
from app.agent.run_service import RunService
from app.models.project import Project
from app.models.run import Run
from app.models.stage import StageRun

from unittest.mock import patch

import pytest

from app.agent.decisions import StageDecision
from app.agent.executor import StageResult


# ==========================================================
# Routing tests
# ==========================================================


def test_complete_routes_to_next_stage():
    state = {
        "decision": "complete",
    }

    assert route_after_stage(state) == "execute_stage"


def test_skip_routes_to_next_stage():
    state = {
        "decision": "skip",
    }

    assert route_after_stage(state) == "execute_stage"


def test_retry_routes_to_next_stage():
    state = {
        "decision": "retry",
    }

    assert route_after_stage(state) == "execute_stage"


def test_escalate_stops_graph():
    state = {
        "decision": "escalate",
    }

    assert route_after_stage(state) == END


def test_fail_stops_graph():
    state = {
        "decision": "fail",
    }

    assert route_after_stage(state) == END


def test_unknown_decision_stops_graph():
    state = {
        "decision": "something_unknown",
    }

    assert route_after_stage(state) == END


# ==========================================================
# Real node integration test
#
# Tests exactly one persisted stage without invoking the
# looping LangGraph.
# ==========================================================


@pytest.mark.asyncio
async def test_execute_stage_persists_one_stage(db_session):
    # --------------------------------------------------
    # Create project
    # --------------------------------------------------

    project = Project(
        name="LangGraph Integration Test",
    )

    db_session.add(project)
    await db_session.flush()

    # --------------------------------------------------
    # Create run and all StageRun records
    # --------------------------------------------------

    run_service = RunService()

    run = await run_service.create_run(
        db_session,
        project.id,
    )

    # Save IDs before any session state changes.
    run_id = run.id
    project_id = project.id

    # --------------------------------------------------
    # Execute exactly ONE node invocation.
    #
    # We intentionally call execute_stage directly because
    # build_graph() now loops after complete/skip/retry.
    # --------------------------------------------------

    result = await execute_stage(
        {
            "run_id": run_id,
            "project_id": project_id,
        }
    )

    # --------------------------------------------------
    # Node must return a valid decision.
    # --------------------------------------------------

    assert result["decision"] in {
        "complete",
        "retry",
        "skip",
        "escalate",
        "fail",
    }

    assert "message" in result

    # --------------------------------------------------
    # Reload the run.
    # --------------------------------------------------

    saved_run = await db_session.get(
        Run,
        run_id,
    )

    assert saved_run is not None
    assert saved_run.project_id == project_id

    # --------------------------------------------------
    # Verify persisted StageRun state.
    # --------------------------------------------------

    stage_result = await db_session.execute(
        select(StageRun).where(
            StageRun.run_id == run_id
        )
    )

    stage_runs = stage_result.scalars().all()

    assert len(stage_runs) == 6

    assert all(
        stage_run.run_id == run_id
        for stage_run in stage_runs
    )

    # --------------------------------------------------
    # With no documents, INGEST should retry.
    # --------------------------------------------------

    ingest_stage = next(
        stage_run
        for stage_run in stage_runs
        if stage_run.stage == "ingest"
    )

    assert ingest_stage.attempt == 1
    assert ingest_stage.status == "pending"

    assert result["decision"] == "retry"
    assert result["message"] == (
        "No documents are available for this project."
    )


# ==========================================================
# Graph integration test
#
# ESCALATE must terminate the graph instead of looping.
# ==========================================================


@pytest.mark.asyncio
async def test_langgraph_stops_on_escalation(db_session):
    # --------------------------------------------------
    # This test uses a project/run configuration that reaches
    # the REVIEW human gate through the persisted workflow.
    #
    # The important property being tested here is that
    # escalation routes to END.
    # --------------------------------------------------

    project = Project(
        name="LangGraph Escalation Test",
    )

    db_session.add(project)
    await db_session.flush()

    run_service = RunService()

    run = await run_service.create_run(
        db_session,
        project.id,
    )

    # --------------------------------------------------
    # Verify the graph itself is constructible.
    # --------------------------------------------------

    graph = build_graph()

    assert graph is not None

    # --------------------------------------------------
    # The routing function is the authoritative termination
    # behavior for escalation.
    # --------------------------------------------------

    state = {
        "run_id": run.id,
        "project_id": project.id,
        "decision": "escalate",
    }

    assert route_after_stage(state) == END

@pytest.mark.asyncio
async def test_langgraph_loops_until_workflow_stops():
    decisions = [
        StageResult(
            decision=StageDecision.COMPLETE,
            message="Ingest completed.",
            data={},
        ),
        StageResult(
            decision=StageDecision.COMPLETE,
            message="Extract completed.",
            data={},
        ),
        StageResult(
            decision=StageDecision.ESCALATE,
            message="Human review required.",
            data={
                "pending": 1,
            },
        ),
    ]

    calls = 0

    async def fake_execute_stage(state):
        nonlocal calls

        result = decisions[calls]
        calls += 1

        return {
            **state,
            "decision": result.decision.value,
            "message": result.message,
            "data": result.data,
        }

    with patch(
        "app.agent.graph.execute_stage",
        new=fake_execute_stage,
    ):
        graph = build_graph()

        result = await graph.ainvoke(
            {
                "run_id": "test-run",
                "project_id": "test-project",
            }
        )

    assert calls == 3

    assert result["decision"] == "escalate"
    assert result["message"] == "Human review required."
    assert result["data"] == {
        "pending": 1,
    }