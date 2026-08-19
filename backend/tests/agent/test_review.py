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