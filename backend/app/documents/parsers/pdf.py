from pathlib import Path

from pypdf import PdfReader

from app.documents.models import ParsedBlock, ParsedDocument, SourceLocation
from app.documents.parser import DocumentParser


class PDFParser(DocumentParser):

    def parse(self, file_path: Path) -> ParsedDocument:
        reader = PdfReader(str(file_path))

        blocks: list[ParsedBlock] = []

        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""

            if not text.strip():
                continue

            blocks.append(
                ParsedBlock(
                    text=text.strip(),
                    location=SourceLocation(
                        page=page_number,
                    ),
                )
            )

        return ParsedDocument(
            filename=file_path.name,
            mime_type="application/pdf",
            blocks=blocks,
        )