import tempfile
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.documents.registry import create_default_registry
from app.documents.service import DocumentService

router = APIRouter(prefix="/projects", tags=["documents"])

parser_registry = create_default_registry()

STORAGE_DIR = Path("storage/uploads")


@router.post("/{project_id}/documents")
async def upload_document(
    project_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required",
        )

    suffix = Path(file.filename).suffix.lower()

    if not suffix:
        raise HTTPException(
            status_code=400,
            detail="File extension is required",
        )

    with tempfile.NamedTemporaryFile(
        suffix=suffix,
        delete=False,
    ) as temp_file:

        temp_path = Path(temp_file.name)

        while chunk := await file.read(1024 * 1024):
            temp_file.write(chunk)

    try:
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

    finally:
        temp_path.unlink(missing_ok=True)