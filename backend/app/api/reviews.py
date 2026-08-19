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

router = APIRouter(
    prefix="/runs",
    tags=["reviews"],
)


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

    if finding.review_decision is not None:
        raise HTTPException(
            status_code=409,
            detail="Finding has already been reviewed",
        )

    finding.review_decision = decision
    finding.status = (
        "approved"
        if decision == "approve"
        else "rejected"
    )
    finding.reviewed_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(finding)

    return {
        "finding_id": str(finding.id),
        "decision": decision,
        "status": finding.status,
        "message": f"Finding {decision}d successfully.",
    }