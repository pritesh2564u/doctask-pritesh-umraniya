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


class WorkflowExecutor:

    def __init__(self) -> None:
        self.run_service = RunService()
        self.handler = StageHandler()

    async def execute_next(
        self,
        db: AsyncSession,
        run_id: UUID,
    ) -> StageResult:
        """
        Execute the next available stage for a run.

        The database is the source of truth. If the process is
        restarted, this method determines the next stage from
        persisted StageRun state instead of starting over.
        """

        run = await self.run_service.get_run(
            db,
            run_id,
        )

        if run is None:
            raise ValueError(
                f"Run {run_id} does not exist"
            )

        # Find the next stage from persisted state.
        stage = await self.get_next_stage(
            db,
            run_id,
        )

        if stage is None:
            return StageResult(
                decision=StageDecision.COMPLETE,
                message="No executable stage remains.",
            )

        # Execute the actual stage handler.
        result = await self.handler.execute(
            db=db,
            project_id=run.project_id,
            run_id=run_id,
            stage=stage,
        )

        # Mark the stage as running and increment attempt.
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
        # COMPLETE
        # --------------------------------------------------

        if result.decision == StageDecision.COMPLETE:

            stage_run.status = StageStatus.COMPLETED

            # The workflow is active again after a successful
            # stage, including after a human-review escalation.
            run.status = "running"

            if stage == StageName.COMMIT:
                run.status = "completed"

        # --------------------------------------------------
        # RETRY
        # --------------------------------------------------

        elif result.decision == StageDecision.RETRY:

            # Do not mark the stage as completed.
            # The next execute call will retry it.
            stage_run.status = StageStatus.PENDING
            stage_run.error = result.message

            run.status = "running"

        # --------------------------------------------------
        # SKIP
        # --------------------------------------------------

        elif result.decision == StageDecision.SKIP:

            stage_run.status = StageStatus.SKIPPED

            run.status = "running"

        # --------------------------------------------------
        # ESCALATE
        # --------------------------------------------------

        elif result.decision == StageDecision.ESCALATE:

            stage_run.status = StageStatus.ESCALATED

            run.status = "escalated"

        # --------------------------------------------------
        # FAIL
        # --------------------------------------------------

        elif result.decision == StageDecision.FAIL:

            stage_run.status = StageStatus.FAILED
            stage_run.error = result.message

            run.status = "failed"

        await db.commit()

        return result

    async def get_next_stage(
        self,
        db: AsyncSession,
        run_id: UUID,
    ) -> StageName | None:
        """
        Determine the next stage from persisted database state.

        Completed/skipped stages are never executed again.

        REVIEW is special because it can be escalated to a human
        and later resumed after the human has made decisions.
        """

        for stage in STAGE_ORDER:

            stage_run = await self.run_service.get_stage(
                db,
                run_id,
                stage,
            )

            if stage_run is None:
                continue

            # ----------------------------------------------
            # Pending stage
            # ----------------------------------------------

            if stage_run.status == StageStatus.PENDING:
                return stage

            # ----------------------------------------------
            # Running stage
            # ----------------------------------------------

            if stage_run.status == StageStatus.RUNNING:
                # A process may have been killed while this stage
                # was running. Re-running it allows recovery.
                return stage

            # ----------------------------------------------
            # Escalated REVIEW stage
            # ----------------------------------------------

            if stage_run.status == StageStatus.ESCALATED:

                # REVIEW is resumable after human decisions.
                if stage == StageName.REVIEW:
                    return stage

                # Other escalations require external intervention.
                return None

            # ----------------------------------------------
            # Failed stage
            # ----------------------------------------------

            if stage_run.status == StageStatus.FAILED:
                return None

            # ----------------------------------------------
            # Completed / skipped
            # ----------------------------------------------

            if stage_run.status in {
                StageStatus.COMPLETED,
                StageStatus.SKIPPED,
            }:
                continue

        return None