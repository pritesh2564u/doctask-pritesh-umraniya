from app.agent.decisions import StageDecision


def test_complete_decision():
    assert StageDecision.COMPLETE == "complete"


def test_retry_decision():
    assert StageDecision.RETRY == "retry"


def test_skip_decision():
    assert StageDecision.SKIP == "skip"


def test_escalate_decision():
    assert StageDecision.ESCALATE == "escalate"


def test_fail_decision():
    assert StageDecision.FAIL == "fail"