import hashlib
import shutil
from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.documents.chunker import create_chunks
from app.documents.models import ParsedDocument
from app.documents.registry import ParserRegistry
from app.models.chunk import DocumentChunk
from app.models.document import Document


class DocumentService:
    def __init__(
        self,
        db: AsyncSession,
        parser_registry: ParserRegistry,
        storage_dir: Path,
    ) -> None:
        self.db = db
        self.parser_registry = parser_registry
        self.storage_dir = storage_dir

    async def ingest(
        self,
        project_id: UUID,
        filename: str,
        content_type: str | None,
        source_file: Path,
    ) -> tuple[Document, ParsedDocument]:

        content = source_file.read_bytes()
        content_hash = hashlib.sha256(content).hexdigest()

        # Check for duplicate document
        result = await self.db.execute(
            select(Document).where(
                Document.project_id == project_id,
                Document.content_hash == content_hash,
            )
        )

        existing_document = result.scalar_one_or_none()

        parser = self.parser_registry.get_parser(source_file)
        parsed_document = parser.parse(source_file)

        if existing_document is not None:
            return existing_document, parsed_document

        # Store original document
        destination_dir = self.storage_dir / str(project_id)
        destination_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        extension = source_file.suffix.lower()

        destination = (
            destination_dir
            / f"{content_hash}{extension}"
        )

        if not destination.exists():
            shutil.copy2(
                source_file,
                destination,
            )

        # Create document
        document = Document(
            project_id=project_id,
            filename=filename,
            mime_type=content_type,
            storage_path=str(destination),
            content_hash=content_hash,
        )

        self.db.add(document)

        # Flush so document.id is available before creating chunks
        await self.db.flush()

        # Create chunks
        chunks = create_chunks(parsed_document.blocks)

        for chunk_data in chunks:
            chunk = DocumentChunk(
                document_id=document.id,
                chunk_index=chunk_data["chunk_index"],
                text=chunk_data["text"],
                start_page=chunk_data["start_page"],
                end_page=chunk_data["end_page"],
                start_paragraph=chunk_data["start_paragraph"],
                end_paragraph=chunk_data["end_paragraph"],
                start_line=chunk_data["start_line"],
                end_line=chunk_data["end_line"],
            )

            self.db.add(chunk)

        await self.db.commit()
        await self.db.refresh(document)

        return document, parsed_document