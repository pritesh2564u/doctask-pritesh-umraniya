def test_workflow_executor_factory_requires_groq_key():
    from app.agent.factory import create_workflow_executor

    # This is intentionally only a construction smoke test.
    # The real API call happens when ANALYZE executes.
    executor = create_workflow_executor()

    assert executor is not None
    assert executor.handler is not None
    assert executor.handler.analysis_service is not None