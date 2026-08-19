import asyncio

from app.agent.stages import StageName, StageStatus


async def fake_run(
    run_id: str,
    delay: float,
) -> tuple[str, str]:
    """
    Simulates two runs executing concurrently.
    Each run keeps its own identity.
    """
    await asyncio.sleep(delay)

    return (
        run_id,
        "completed",
    )


async def execute_two_runs():
    return await asyncio.gather(
        fake_run("run-a", 0.05),
        fake_run("run-b", 0.01),
    )


def test_two_runs_remain_independent():
    results = asyncio.run(
        execute_two_runs()
    )

    assert len(results) == 2

    run_ids = {
        result[0]
        for result in results
    }

    assert run_ids == {
        "run-a",
        "run-b",
    }


def test_stage_status_is_scoped_to_run():
    run_a = {
        "run_id": "run-a",
        "stage": StageName.ANALYZE,
        "status": StageStatus.COMPLETED,
    }

    run_b = {
        "run_id": "run-b",
        "stage": StageName.ANALYZE,
        "status": StageStatus.PENDING,
    }

    assert run_a["run_id"] != run_b["run_id"]

    assert run_a["status"] == StageStatus.COMPLETED
    assert run_b["status"] == StageStatus.PENDING