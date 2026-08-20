from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.finding import Finding
from app.models.run import Run
from app.models.chunk import DocumentChunk
from app.models.document import Document
from app.agent.stages import StageName, StageStatus
from app.models.stage import StageRun
from app.agent.graph import build_graph

router = APIRouter(
    prefix="/runs",
    tags=["reviews"],
)

workflow_graph = build_graph()

class ReviewDecisionRequest(BaseModel):
    decision: str


@router.get("/{run_id}/review")
async def get_review(
    run_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Run).where(Run.id == run_id)
    )

    run = result.scalar_one_or_none()

    if run is None:
        raise HTTPException(
            status_code=404,
            detail="Run not found",
        )

    result = await db.execute(
        select(Finding)
        .where(Finding.run_id == run_id)
        .order_by(Finding.created_at)
    )

    findings = result.scalars().all()

    results = []

    for finding in findings:
        result = await db.execute(
            select(DocumentChunk, Document)
            .join(
                Document,
                Document.id == DocumentChunk.document_id,
            )
            .where(DocumentChunk.id == finding.chunk_id)
        )

        row = result.first()

        source = None

        if row:
            chunk, document = row

            source = {
                "document_id": str(document.id),
                "filename": document.filename,
                "chunk_id": str(chunk.id),
                "start_page": chunk.start_page,
                "end_page": chunk.end_page,
                "start_paragraph": chunk.start_paragraph,
                "end_paragraph": chunk.end_paragraph,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "quote": chunk.text,
            }

        results.append(
            {
                "finding_id": str(finding.id),
                "title": finding.title,
                "description": finding.description,
                "status": finding.status,
                "review_decision": finding.review_decision,
                "source": source,
            }
        )

    return {
        "run_id": str(run_id),
        "status": run.status,
        "findings": results,
    }


@router.post("/{run_id}/review/{finding_id}")
async def review_finding(
    run_id: UUID,
    finding_id: UUID,
    request: ReviewDecisionRequest,
    db: AsyncSession = Depends(get_db),
):
    decision = request.decision.lower()

    if decision not in {"approve", "reject"}:
        raise HTTPException(
            status_code=400,
            detail="Decision must be 'approve' or 'reject'",
        )

    # --------------------------------------------------
    # Verify finding belongs to this run.
    # --------------------------------------------------

    result = await db.execute(
        select(Finding).where(
            Finding.id == finding_id,
            Finding.run_id == run_id,
        )
    )

    finding = result.scalar_one_or_none()

    if finding is None:
        raise HTTPException(
            status_code=404,
            detail="Finding not found",
        )

    # --------------------------------------------------
    # Prevent duplicate review.
    # --------------------------------------------------

    if finding.review_decision is not None:
        raise HTTPException(
            status_code=409,
            detail="Finding has already been reviewed",
        )

    # --------------------------------------------------
    # Save human decision.
    # --------------------------------------------------

    finding.review_decision = decision

    finding.status = (
        "approved"
        if decision == "approve"
        else "rejected"
    )

    finding.reviewed_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(finding)

    # --------------------------------------------------
    # Check whether ALL findings have been reviewed.
    # --------------------------------------------------

    result = await db.execute(
        select(Finding).where(
            Finding.run_id == run_id,
        )
    )

    findings = result.scalars().all()

    all_reviewed = (
        len(findings) > 0
        and all(
            item.review_decision is not None
            for item in findings
        )
    )

    # --------------------------------------------------
    # If some findings are still waiting for review,
    # do NOT resume the workflow.
    # --------------------------------------------------

    if not all_reviewed:
        return {
            "finding_id": str(finding.id),
            "decision": decision,
            "status": finding.status,
            "message": (
                f"Finding {decision}d successfully. "
                "Waiting for remaining human reviews."
            ),
            "workflow_resumed": False,
        }

    # --------------------------------------------------
    # ALL findings have now been reviewed.
    #
    # Automatically resume the persisted workflow.
    # --------------------------------------------------

    result = await db.execute(
        select(Run).where(
            Run.id == run_id,
        )
    )

    run = result.scalar_one_or_none()

    if run is None:
        raise HTTPException(
            status_code=404,
            detail="Run not found",
        )

    # --------------------------------------------------
    # Safety check.
    #
    # Only resume if the workflow is actually waiting
    # for human review.
    # --------------------------------------------------

    review_stage_result = await db.execute(
        select(StageRun).where(
            StageRun.run_id == run_id,
            StageRun.stage == StageName.REVIEW,
        )
    )

    review_stage = (
        review_stage_result.scalar_one_or_none()
    )

    if review_stage is None:
        raise HTTPException(
            status_code=500,
            detail="Review stage not found",
        )

    if review_stage.status != StageStatus.ESCALATED:
        return {
            "finding_id": str(finding.id),
            "decision": decision,
            "status": finding.status,
            "message": (
                f"Finding {decision}d successfully. "
                "Workflow does not require resume."
            ),
            "workflow_resumed": False,
        }

    # --------------------------------------------------
    # Re-open the REVIEW stage.
    #
    # The executor treats an ESCALATED stage as a hard
    # stop. Since all human decisions are now complete,
    # change it back to PENDING so the executor can
    # execute REVIEW again.
    # --------------------------------------------------

    review_stage.status = StageStatus.PENDING
    run.status = "running"

    await db.commit()

    # --------------------------------------------------
    # Resume the persisted workflow.
    #
    # REVIEW will now be selected by get_next_stage().
    #
    # REVIEW
    #   -> COMPLETE
    #   -> COMMIT
    # --------------------------------------------------

    try:
        workflow_result = await workflow_graph.ainvoke(
            {
                "run_id": run_id,
                "project_id": run.project_id,
            }
        )

    except Exception as exc:
        # The human decision has already been safely
        # persisted. Do not roll it back.
        #
        # Return an explicit error so the frontend can
        # display that review succeeded but workflow
        # resume failed.
        return {
            "finding_id": str(finding.id),
            "decision": decision,
            "status": finding.status,
            "message": (
                "Finding reviewed successfully, but "
                f"workflow resume failed: {exc}"
            ),
            "workflow_resumed": False,
            "workflow_error": str(exc),
        }

    # --------------------------------------------------
    # Return both review and workflow information.
    # --------------------------------------------------

    return {
        "finding_id": str(finding.id),
        "decision": decision,
        "status": finding.status,
        "message": (
            f"Finding {decision}d successfully. "
            "All findings have been reviewed and "
            "the workflow has resumed."
        ),
        "workflow_resumed": True,
        "workflow_decision": workflow_result.get(
            "decision"
        ),
        "workflow_message": workflow_result.get(
            "message"
        ),
        "workflow_data": workflow_result.get(
            "data",
            {},
        ),
    }