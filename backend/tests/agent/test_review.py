import pytest

from app.agent.decisions import StageDecision


def test_review_decisions_are_independent():
    decisions = {
        "finding_1": "approve",
        "finding_2": "reject",
        "finding_3": None,
    }

    assert decisions["finding_1"] == "approve"
    assert decisions["finding_2"] == "reject"
    assert decisions["finding_3"] is None


def test_pending_finding_blocks_commit():
    findings = [
        {"review_decision": "approve"},
        {"review_decision": "reject"},
        {"review_decision": None},
    ]

    pending = [
        finding
        for finding in findings
        if finding["review_decision"] is None
    ]

    assert len(pending) == 1


def test_all_findings_reviewed_allows_commit():
    findings = [
        {"review_decision": "approve"},
        {"review_decision": "reject"},
    ]

    pending = [
        finding
        for finding in findings
        if finding["review_decision"] is None
    ]

    assert len(pending) == 0


def test_only_approved_findings_are_committed():
    findings = [
        {"review_decision": "approve"},
        {"review_decision": "reject"},
        {"review_decision": "approve"},
    ]

    approved = [
        finding
        for finding in findings
        if finding["review_decision"] == "approve"
    ]

    rejected = [
        finding
        for finding in findings
        if finding["review_decision"] == "reject"
    ]

    assert len(approved) == 2
    assert len(rejected) == 1

@pytest.mark.asyncio
async def test_open_reconciliation_blocks_commit(db_session):
    from uuid import uuid4

    from app.agent.stage_handlers import StageHandler
    from app.models.project import Project
    from app.models.reconciliation import ReconciliationResult
    from app.models.run import Run

    project = Project(
        name=f"Commit Conflict Test {uuid4()}",
    )

    db_session.add(project)
    await db_session.flush()

    run = Run(
        project_id=project.id,
        status="running",
        current_stage="commit",
    )

    db_session.add(run)
    await db_session.flush()

    conflict = ReconciliationResult(
        run_id=run.id,
        conflict_type="status_conflict",
        description="Conflicting status evidence.",
        status="open",
    )

    db_session.add(conflict)
    await db_session.commit()

    handler = StageHandler()

    result = await handler.commit(
        db=db_session,
        project_id=project.id,
        run_id=run.id,
    )

    assert result.decision == StageDecision.ESCALATE
    assert result.data["conflict_count"] == 1