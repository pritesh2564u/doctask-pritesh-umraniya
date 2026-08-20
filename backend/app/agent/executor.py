from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.decisions import StageDecision
from app.agent.run_service import RunService
from app.agent.stage_handlers import StageHandler, StageResult
from app.agent.stages import (
    STAGE_ORDER,
    StageName,
    StageStatus,
)
from datetime import datetime, timezone
from decimal import Decimal

MAX_STAGE_ATTEMPTS = 3
# USD per 1 million tokens.
#
# Configure these according to the Groq model used by the project.
# These defaults are intentionally zero so the system never invents
# a monetary cost when pricing has not been configured.
INPUT_COST_PER_1M = Decimal("0.075")
OUTPUT_COST_PER_1M = Decimal("0.30")

class WorkflowExecutor:

    def __init__(
        self,
        handler: StageHandler | None = None,
    ) -> None:
        self.run_service = RunService()
        self.handler = handler or StageHandler()

    async def execute_next(
        self,
        db: AsyncSession,
        run_id: UUID,
    ) -> StageResult:

        run = await self.run_service.get_run(
            db,
            run_id,
        )

        if run is None:
            raise ValueError(
                f"Run {run_id} does not exist"
            )

        stage = await self.get_next_stage(
            db,
            run_id,
        )

        if stage is None:

            if run.status == "escalated":
                return StageResult(
                    decision=StageDecision.ESCALATE,
                    message="Workflow is waiting for human review.",
                    data={
                        "workflow_complete": False,
                    },
                )

            if run.status == "failed":
                return StageResult(
                    decision=StageDecision.FAIL,
                    message="Workflow cannot continue because a stage failed.",
                    data={
                        "workflow_complete": False,
                    },
                )

            return StageResult(
                decision=StageDecision.COMPLETE,
                message="No executable stage remains.",
                data={
                    "workflow_complete": True,
                },
            )

        # --------------------------------------------------
        # Start stage
        # --------------------------------------------------

        await self.run_service.start_stage(
            db,
            run_id,
            stage,
        )

        stage_run = await self.run_service.get_stage(
            db,
            run_id,
            stage,
        )

        if stage_run is None:
            raise ValueError(
                f"StageRun for {stage} does not exist"
            )

        # --------------------------------------------------
        # Execute stage + usage tracking
        # --------------------------------------------------

        stage_run.started_at = datetime.now(timezone.utc)

        result = await self.handler.execute(
            db=db,
            project_id=run.project_id,
            run_id=run_id,
            stage=stage,
        )

        stage_run.completed_at = datetime.now(timezone.utc)

        stage_run.duration_ms = int(
            (
                stage_run.completed_at
                - stage_run.started_at
            ).total_seconds()
            * 1000
        )

        usage = (result.data or {}).get(
            "usage",
            {},
        )

        input_tokens = int(
            usage.get("input_tokens", 0)
        )

        output_tokens = int(
            usage.get("output_tokens", 0)
        )

        total_tokens = int(
            usage.get(
                "total_tokens",
                input_tokens + output_tokens,
            )
        )

        input_cost = (
            Decimal(input_tokens)
            / Decimal("1000000")
            * INPUT_COST_PER_1M
        )

        output_cost = (
            Decimal(output_tokens)
            / Decimal("1000000")
            * OUTPUT_COST_PER_1M
        )

        estimated_cost = input_cost + output_cost

        stage_run.input_tokens = input_tokens
        stage_run.output_tokens = output_tokens
        stage_run.total_tokens = total_tokens
        stage_run.estimated_cost_usd = estimated_cost

        # --------------------------------------------------
        # COMPLETE
        # --------------------------------------------------

        if result.decision == StageDecision.COMPLETE:

            stage_run.status = StageStatus.COMPLETED

            stage_run.message = result.message
            stage_run.details = result.data or {}

            run.status = "running"

            next_stage = await self.get_next_stage(
                db,
                run_id,
            )

            workflow_complete = next_stage is None

            if workflow_complete:
                run.status = "completed"

            result = StageResult(
                decision=StageDecision.COMPLETE,
                message=result.message,
                data={
                    **(result.data or {}),
                    "workflow_complete": workflow_complete,
                },
            )

            stage_run.details = result.data or {}

        # --------------------------------------------------
        # RETRY
        # --------------------------------------------------

        elif result.decision == StageDecision.RETRY:

            stage_run.message = result.message
            stage_run.details = result.data or {}

            if stage_run.attempt >= MAX_STAGE_ATTEMPTS:

                stage_run.status = StageStatus.FAILED

                stage_run.error = (
                    f"Maximum retry attempts ({MAX_STAGE_ATTEMPTS}) "
                    f"reached. Last error: {result.message}"
                )

                stage_run.message = stage_run.error

                run.status = "failed"

                result = StageResult(
                    decision=StageDecision.FAIL,
                    message=stage_run.error,
                    data={
                        **(result.data or {}),
                        "attempt": stage_run.attempt,
                        "max_attempts": MAX_STAGE_ATTEMPTS,
                    },
                )

                stage_run.details = result.data or {}

            else:

                stage_run.status = StageStatus.PENDING
                stage_run.error = result.message

                run.status = "running"

        # --------------------------------------------------
        # SKIP
        # --------------------------------------------------

        elif result.decision == StageDecision.SKIP:

            stage_run.status = StageStatus.SKIPPED

            stage_run.message = result.message
            stage_run.details = result.data or {}

            run.status = "running"

            next_stage = await self.get_next_stage(
                db,
                run_id,
            )

            workflow_complete = next_stage is None

            if workflow_complete:
                run.status = "completed"

            result = StageResult(
                decision=StageDecision.SKIP,
                message=result.message,
                data={
                    **(result.data or {}),
                    "workflow_complete": workflow_complete,
                },
            )

            stage_run.details = result.data or {}

        # --------------------------------------------------
        # ESCALATE
        # --------------------------------------------------

        elif result.decision == StageDecision.ESCALATE:

            stage_run.status = StageStatus.ESCALATED

            stage_run.message = result.message
            stage_run.details = result.data or {}

            run.status = "escalated"

        # --------------------------------------------------
        # FAIL
        # --------------------------------------------------

        elif result.decision == StageDecision.FAIL:

            stage_run.status = StageStatus.FAILED

            stage_run.message = result.message
            stage_run.details = result.data or {}
            stage_run.error = result.message

            run.status = "failed"

        # --------------------------------------------------
        # Persist state
        # --------------------------------------------------

        await db.commit()

        return result

    async def get_next_stage(
        self,
        db: AsyncSession,
        run_id: UUID,
    ) -> StageName | None:

        for stage in STAGE_ORDER:

            stage_run = await self.run_service.get_stage(
                db,
                run_id,
                stage,
            )

            if stage_run is None:
                continue

            # Pending
            if stage_run.status == StageStatus.PENDING:
                return stage

            # Running
            if stage_run.status == StageStatus.RUNNING:
                return stage

            # Escalated
            if stage_run.status == StageStatus.ESCALATED:
                return None

            # Failed
            if stage_run.status == StageStatus.FAILED:
                return None

            # Completed / skipped
            if stage_run.status in {
                StageStatus.COMPLETED,
                StageStatus.SKIPPED,
            }:
                continue

        return None