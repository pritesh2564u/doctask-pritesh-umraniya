import hashlib
import shutil
from pathlib import Path
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.documents.registry import ParserRegistry
from app.documents.models import ParsedDocument
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

        extension = source_file.suffix.lower()

        parser = self.parser_registry.get_parser(source_file)

        parsed_document = parser.parse(source_file)

        destination_dir = self.storage_dir / str(project_id)
        destination_dir.mkdir(parents=True, exist_ok=True)

        destination = destination_dir / f"{content_hash}{extension}"

        if not destination.exists():
            shutil.copy2(source_file, destination)

        document = Document(
            project_id=project_id,
            filename=filename,
            mime_type=content_type,
            storage_path=str(destination),
            content_hash=content_hash,
        )

        self.db.add(document)
        await self.db.commit()
        await self.db.refresh(document)

        return document, parsed_document