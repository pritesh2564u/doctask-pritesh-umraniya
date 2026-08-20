from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.decisions import StageDecision
from app.agent.stages import StageName
from app.models.chunk import DocumentChunk
from app.models.document import Document
from app.models.finding import Finding
from app.models.reconciliation import ReconciliationResult
from app.agent.llm_service import AnalysisService

@dataclass
class StageResult:
    decision: StageDecision
    message: str
    data: dict | None = None


class StageHandler:
    def __init__(
        self,
        analysis_service: AnalysisService | None = None,
    ) -> None:
        self.analysis_service = analysis_service

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

        if self.analysis_service is None:
            return StageResult(
                decision=StageDecision.FAIL,
                message="Analysis service is not configured.",
            )

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

        input_tokens = 0
        output_tokens = 0
        total_tokens = 0

        for chunk in chunks:

            analysis_result = await self.analysis_service.analyze(
                chunk.text
            )

            analysis = analysis_result.finding
            usage = analysis_result.usage

            input_tokens += usage.input_tokens
            output_tokens += usage.output_tokens
            total_tokens += usage.total_tokens

            if not analysis.is_risk:
                continue

            # --------------------------------------------------
            # Preserve run_id + chunk_id ownership in our code.
            # The LLM never controls these values.
            # --------------------------------------------------

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
                    title=analysis.title,
                    description=analysis.description,
                    status="pending",
                )

                db.add(finding)

            findings.append(
                {
                    "chunk_id": str(chunk.id),
                    "title": analysis.title,
                    "description": analysis.description,
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
                decision=StageDecision.COMPLETE,
                message=(
                    "Analysis completed. "
                    "No potential delivery risks were identified."
                ),
                data={
                    "finding_count": 0,
                    "findings": [],
                    "usage": {
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "total_tokens": total_tokens,
                    },
                },
            )

        return StageResult(
            decision=StageDecision.COMPLETE,
            message=(
                f"Identified {len(findings)} potential finding(s)."
            ),
            data={
                "findings": findings,
                "finding_count": len(findings),
                "usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens,
                },
            },
        )

    async def reconcile(
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
                Document.project_id == project_id,
            )
        )

        chunks = result.scalars().all()

        if not chunks:
            return StageResult(
                decision=StageDecision.SKIP,
                message="No evidence requires reconciliation.",
                data={
                    "conflicts": [],
                    "conflict_count": 0,
                },
            )

        observations: dict[str, list[str]] = {
            "completed": [],
            "in_progress": [],
            "at_risk": [],
        }

        for chunk in chunks:
            text = chunk.text.lower()

            if "completed" in text:
                observations["completed"].append(
                    str(chunk.id)
                )

            if "in progress" in text:
                observations["in_progress"].append(
                    str(chunk.id)
                )

            if "at risk" in text:
                observations["at_risk"].append(
                    str(chunk.id)
                )

        conflicts = []

        # --------------------------------------------------
        # completed vs in_progress
        # --------------------------------------------------

        if (
            observations["completed"]
            and observations["in_progress"]
        ):
            conflicts.append(
                {
                    "statuses": [
                        "completed",
                        "in_progress",
                    ],
                    "chunk_ids": (
                        observations["completed"]
                        + observations["in_progress"]
                    ),
                }
            )

        # --------------------------------------------------
        # completed vs at_risk
        # --------------------------------------------------

        if (
            observations["completed"]
            and observations["at_risk"]
        ):
            conflicts.append(
                {
                    "statuses": [
                        "completed",
                        "at_risk",
                    ],
                    "chunk_ids": (
                        observations["completed"]
                        + observations["at_risk"]
                    ),
                }
            )

        for conflict in conflicts:
            conflict_type = "status_conflict"

            description = (
                "Conflicting project status evidence detected: "
                f"{', '.join(conflict['statuses'])}. "
                f"Affected chunks: "
                f"{', '.join(conflict['chunk_ids'])}."
            )

            existing = await db.execute(
                select(ReconciliationResult).where(
                    ReconciliationResult.run_id == run_id,
                    ReconciliationResult.conflict_type == conflict_type,
                    ReconciliationResult.description == description,
                )
            )

            if existing.scalar_one_or_none() is None:
                db.add(
                    ReconciliationResult(
                        run_id=run_id,
                        conflict_type=conflict_type,
                        description=description,
                        status="open",
                    )
                )

        await db.commit()

        return StageResult(
            decision=StageDecision.COMPLETE,
            message=(
                f"Evidence reconciliation completed. "
                f"Found {len(conflicts)} conflict(s)."
            ),
            data={
                "conflicts": conflicts,
                "conflict_count": len(conflicts),
            },
        )

    async def review(
        self,
        db: AsyncSession,
        project_id: UUID,
        run_id: UUID,
    ) -> StageResult:

        # --------------------------------------------------
        # Check unresolved reconciliation conflicts first.
        # --------------------------------------------------

        result = await db.execute(
            select(ReconciliationResult).where(
                ReconciliationResult.run_id == run_id,
                ReconciliationResult.status == "open",
            )
        )

        reconciliation_results = result.scalars().all()

        if reconciliation_results:
            return StageResult(
                decision=StageDecision.ESCALATE,
                message=(
                    f"{len(reconciliation_results)} "
                    "reconciliation conflict(s) require "
                    "resolution before review can continue."
                ),
                data={
                    "conflict_count": len(
                        reconciliation_results
                    ),
                    "conflicts": [
                        {
                            "id": str(item.id),
                            "conflict_type": item.conflict_type,
                            "description": item.description,
                            "status": item.status,
                        }
                        for item in reconciliation_results
                    ],
                },
            )

        # --------------------------------------------------
        # Load findings belonging ONLY to this run.
        # --------------------------------------------------

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

        # --------------------------------------------------
        # Human gate is still open.
        # --------------------------------------------------

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

        # --------------------------------------------------
        # Unresolved reconciliation conflicts block commit.
        # --------------------------------------------------

        result = await db.execute(
            select(ReconciliationResult).where(
                ReconciliationResult.run_id == run_id,
                ReconciliationResult.status == "open",
            )
        )

        open_conflicts = result.scalars().all()

        if open_conflicts:
            return StageResult(
                decision=StageDecision.ESCALATE,
                message=(
                    "Commit blocked because unresolved "
                    "reconciliation conflict(s) remain."
                ),
                data={
                    "conflict_count": len(open_conflicts),
                    "conflicts": [
                        {
                            "id": str(conflict.id),
                            "conflict_type": conflict.conflict_type,
                            "description": conflict.description,
                        }
                        for conflict in open_conflicts
                    ],
                },
            )

        result = await db.execute(
            select(Finding).where(
                Finding.run_id == run_id
            )
        )

        findings = result.scalars().all()

        if not findings:
            return StageResult(
                decision=StageDecision.COMPLETE,
                message="Commit completed. There are no findings to commit.",
                data={
                    "committed": 0,
                    "rejected": 0,
                },
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
                run_id=run_id,
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

    async def resolve_reconciliation(
        self,
        db: AsyncSession,
        run_id: UUID,
        reconciliation_id: UUID,
    ) -> StageResult:

        result = await db.execute(
            select(ReconciliationResult).where(
                ReconciliationResult.id == reconciliation_id,
                ReconciliationResult.run_id == run_id,
            )
        )

        reconciliation = result.scalar_one_or_none()

        if reconciliation is None:
            return StageResult(
                decision=StageDecision.FAIL,
                message="Reconciliation result not found for this run.",
            )

        if reconciliation.status == "resolved":
            return StageResult(
                decision=StageDecision.COMPLETE,
                message="Reconciliation conflict is already resolved.",
                data={
                    "reconciliation_id": str(
                        reconciliation.id
                    ),
                    "status": reconciliation.status,
                },
            )

        reconciliation.status = "resolved"

        await db.commit()
        await db.refresh(reconciliation)

        return StageResult(
            decision=StageDecision.COMPLETE,
            message="Reconciliation conflict resolved.",
            data={
                "reconciliation_id": str(
                    reconciliation.id
                ),
                "status": reconciliation.status,
            },
        )