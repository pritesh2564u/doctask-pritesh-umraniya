from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.decisions import StageDecision
from app.agent.stages import StageName
from app.models.chunk import DocumentChunk
from app.models.document import Document
from app.models.finding import Finding

@dataclass
class StageResult:
    decision: StageDecision
    message: str
    data: dict | None = None


class StageHandler:
    """
    Implements the actual behavior of each agent stage.

    The handlers intentionally do not call an LLM yet.
    They operate on persisted document/evidence data so the
    workflow remains testable without an API key.
    """

    async def ingest(
        self,
        db: AsyncSession,
        project_id: UUID,
    ) -> StageResult:

        result = await db.execute(
            select(Document).where(
                Document.project_id == project_id
            )
        )

        documents = result.scalars().all()

        if not documents:
            return StageResult(
                decision=StageDecision.RETRY,
                message="No documents are available for this project.",
            )

        return StageResult(
            decision=StageDecision.COMPLETE,
            message=f"Discovered {len(documents)} document(s).",
            data={
                "document_count": len(documents),
                "document_ids": [
                    str(document.id)
                    for document in documents
                ],
            },
        )

    async def extract(
        self,
        db: AsyncSession,
        project_id: UUID,
    ) -> StageResult:

        result = await db.execute(
            select(DocumentChunk)
            .join(
                Document,
                Document.id == DocumentChunk.document_id,
            )
            .where(
                Document.project_id == project_id
            )
        )

        chunks = result.scalars().all()

        if not chunks:
            return StageResult(
                decision=StageDecision.RETRY,
                message="No document chunks are available.",
            )

        return StageResult(
            decision=StageDecision.COMPLETE,
            message=f"Extracted {len(chunks)} evidence chunk(s).",
            data={
                "chunk_count": len(chunks),
            },
        )

    async def analyze(
        self,
        db: AsyncSession,
        project_id: UUID,
        run_id: UUID,
    ) -> StageResult:

        result = await db.execute(
            select(DocumentChunk)
            .join(
                Document,
                Document.id == DocumentChunk.document_id,
            )
            .where(
                Document.project_id == project_id
            )
        )

        chunks = result.scalars().all()

        if not chunks:
            return StageResult(
                decision=StageDecision.RETRY,
                message="Analysis cannot run without evidence.",
            )

        findings = []

        risk_keywords = [
            "risk",
            "at risk",
            "delay",
            "delayed",
            "blocked",
            "blocker",
            "overdue",
            "issue",
            "critical",
        ]

        for chunk in chunks:

            text_lower = chunk.text.lower()

            matched_keywords = [
                keyword
                for keyword in risk_keywords
                if keyword in text_lower
            ]

            if not matched_keywords:
                continue

            # Check whether this finding already exists.
            existing_result = await db.execute(
                select(Finding).where(
                    Finding.run_id == run_id,
                    Finding.chunk_id == chunk.id,
                )
            )

            existing_finding = (
                existing_result.scalar_one_or_none()
            )

            if existing_finding is None:

                finding = Finding(
                    run_id=run_id,
                    chunk_id=chunk.id,
                    title="Potential delivery risk",
                    description=chunk.text,
                    status="pending",
                )

                db.add(finding)

            findings.append(
                {
                    "chunk_id": str(chunk.id),
                    "text": chunk.text,
                    "matched_keywords": matched_keywords,
                    "source": {
                        "start_page": chunk.start_page,
                        "end_page": chunk.end_page,
                        "start_paragraph": chunk.start_paragraph,
                        "end_paragraph": chunk.end_paragraph,
                        "start_line": chunk.start_line,
                        "end_line": chunk.end_line,
                    },
                }
            )

        await db.commit()

        if not findings:
            return StageResult(
                decision=StageDecision.SKIP,
                message="No potential delivery risks were identified.",
                data={
                    "finding_count": 0,
                },
            )

        return StageResult(
            decision=StageDecision.COMPLETE,
            message=f"Identified {len(findings)} potential finding(s).",
            data={
                "findings": findings,
                "finding_count": len(findings),
            },
        )
    
    async def reconcile(
        self,
        db: AsyncSession,
        project_id: UUID,
    ) -> StageResult:

        result = await db.execute(
            select(DocumentChunk)
            .join(
                Document,
                Document.id == DocumentChunk.document_id,
            )
            .where(
                Document.project_id == project_id
            )
        )

        chunks = result.scalars().all()

        if not chunks:
            return StageResult(
                decision=StageDecision.SKIP,
                message="No evidence requires reconciliation.",
            )

        # Conflict detection will be expanded later.
        # For now, identify documents that contain
        # potentially conflicting status terminology.
        statuses = []

        for chunk in chunks:
            text = chunk.text.lower()

            if "completed" in text:
                statuses.append(
                    {
                        "chunk_id": str(chunk.id),
                        "status": "completed",
                    }
                )

            if "in progress" in text:
                statuses.append(
                    {
                        "chunk_id": str(chunk.id),
                        "status": "in_progress",
                    }
                )

            if "at risk" in text:
                statuses.append(
                    {
                        "chunk_id": str(chunk.id),
                        "status": "at_risk",
                    }
                )

        return StageResult(
            decision=StageDecision.COMPLETE,
            message="Evidence reconciliation completed.",
            data={
                "status_observations": statuses,
            },
        )

    async def review(
        self,
        db: AsyncSession,
        project_id: UUID,
        run_id: UUID,
    ) -> StageResult:

        result = await db.execute(
            select(Finding).where(
                Finding.run_id == run_id
            )
        )

        findings = result.scalars().all()

        if not findings:
            return StageResult(
                decision=StageDecision.SKIP,
                message="No findings require human review.",
                data={
                    "finding_count": 0,
                },
            )

        pending = [
            finding
            for finding in findings
            if finding.review_decision is None
        ]

        approved = [
            finding
            for finding in findings
            if finding.review_decision == "approve"
        ]

        rejected = [
            finding
            for finding in findings
            if finding.review_decision == "reject"
        ]

        # Human gate is still open.
        if pending:
            return StageResult(
                decision=StageDecision.ESCALATE,
                message=(
                    f"{len(pending)} finding(s) still require "
                    "human review."
                ),
                data={
                    "total": len(findings),
                    "pending": len(pending),
                    "approved": len(approved),
                    "rejected": len(rejected),
                },
            )

        return StageResult(
            decision=StageDecision.COMPLETE,
            message="All findings have been explicitly reviewed.",
            data={
                "total": len(findings),
                "pending": 0,
                "approved": len(approved),
                "rejected": len(rejected),
            },
        )

    async def commit(
        self,
        db: AsyncSession,
        project_id: UUID,
        run_id: UUID,
    ) -> StageResult:

        result = await db.execute(
            select(Finding).where(
                Finding.run_id == run_id
            )
        )

        findings = result.scalars().all()

        if not findings:
            return StageResult(
                decision=StageDecision.SKIP,
                message="Nothing to commit.",
            )

        # NEVER commit while a human decision is missing.
        pending = [
            finding
            for finding in findings
            if finding.review_decision is None
        ]

        if pending:
            return StageResult(
                decision=StageDecision.ESCALATE,
                message=(
                    "Commit blocked because some findings "
                    "have not been reviewed."
                ),
                data={
                    "pending_findings": [
                        str(finding.id)
                        for finding in pending
                    ],
                },
            )

        approved = [
            finding
            for finding in findings
            if finding.review_decision == "approve"
        ]

        rejected = [
            finding
            for finding in findings
            if finding.review_decision == "reject"
        ]

        # Mark only approved findings as committed.
        for finding in approved:
            finding.status = "committed"

        for finding in rejected:
            finding.status = "rejected"

        await db.commit()

        return StageResult(
            decision=StageDecision.COMPLETE,
            message=(
                f"Committed {len(approved)} approved finding(s); "
                f"{len(rejected)} rejected finding(s) were excluded."
            ),
            data={
                "committed": len(approved),
                "rejected": len(rejected),
            },
        )

    async def execute(
        self,
        db: AsyncSession,
        project_id: UUID,
        run_id: UUID,
        stage: StageName,
    ) -> StageResult:

        if stage == StageName.INGEST:
            return await self.ingest(
                db,
                project_id,
            )

        if stage == StageName.EXTRACT:
            return await self.extract(
                db,
                project_id,
            )

        if stage == StageName.ANALYZE:
            return await self.analyze(
                db,
                project_id,
                run_id,
            )

        if stage == StageName.RECONCILE:
            return await self.reconcile(
                db,
                project_id,
            )

        if stage == StageName.REVIEW:
            return await self.review(
                db,
                project_id,
                run_id,
            )

        if stage == StageName.COMMIT:
            return await self.commit(
                db,
                project_id,
                run_id,
            )

        return StageResult(
            decision=StageDecision.FAIL,
            message=f"No handler exists for stage: {stage}",
        )