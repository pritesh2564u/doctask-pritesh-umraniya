import tempfile
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.documents.registry import create_default_registry
from app.documents.service import DocumentService
from app.models.project import Project
from app.models.document import Document

router = APIRouter(
    prefix="/projects",
    tags=["documents"],
)

parser_registry = create_default_registry()

STORAGE_DIR = Path("storage/uploads")
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB


@router.post("/{project_id}/documents")
async def upload_document(
    project_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    # Validate filename
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required",
        )

    # Validate project exists
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )

    project = result.scalar_one_or_none()

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    # Validate file extension
    suffix = Path(file.filename).suffix.lower()

    if not suffix:
        raise HTTPException(
            status_code=400,
            detail="File extension is required",
        )

    # Save upload temporarily
    temp_path: Path | None = None
    total_size = 0

    try:
        with tempfile.NamedTemporaryFile(
            suffix=suffix,
            delete=False,
        ) as temp_file:
            temp_path = Path(temp_file.name)

            while chunk := await file.read(1024 * 1024):
                total_size += len(chunk)

                if total_size > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail="File size exceeds the 25 MB limit",
                    )

                temp_file.write(chunk)

        service = DocumentService(
            db=db,
            parser_registry=parser_registry,
            storage_dir=STORAGE_DIR,
        )

        document, parsed = await service.ingest(
            project_id=project_id,
            filename=file.filename,
            content_type=file.content_type,
            source_file=temp_path,
        )

        return {
            "id": str(document.id),
            "filename": document.filename,
            "mime_type": document.mime_type,
            "content_hash": document.content_hash,
            "blocks": len(parsed.blocks),
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=415,
            detail=str(exc),
        ) from exc

    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)

        await file.close()

@router.get("/{project_id}/documents")
async def list_documents(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Document)
        .where(Document.project_id == project_id)
        .order_by(Document.created_at.desc())
    )

    documents = result.scalars().all()

    return {
        "documents": [
            {
                "id": str(document.id),
                "filename": document.filename,
                "mime_type": document.mime_type,
                "content_hash": document.content_hash,
                "document_type": document.document_type,
                "created_at": document.created_at,
            }
            for document in documents
        ],
    }

@router.delete(
    "/{project_id}/documents/{document_id}",
    status_code=204,
)
async def delete_document(
    project_id: UUID,
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    # --------------------------------------------------
    # Verify document belongs to project.
    # --------------------------------------------------

    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.project_id == project_id,
        )
    )

    document = result.scalar_one_or_none()

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    # --------------------------------------------------
    # Remove physical file.
    # --------------------------------------------------

    if document.storage_path:
        Path(
            document.storage_path
        ).unlink(missing_ok=True)

    # --------------------------------------------------
    # Remove database record.
    #
    # Dependent chunks should be removed through the
    # database FK cascade.
    # --------------------------------------------------

    await db.delete(document)

    await db.commit()

    return None