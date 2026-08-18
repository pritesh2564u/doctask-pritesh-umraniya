from pathlib import Path

from app.documents.models import ParsedBlock, ParsedDocument, SourceLocation
from app.documents.parser import DocumentParser


class TextParser(DocumentParser):

    def parse(self, file_path: Path) -> ParsedDocument:
        text = file_path.read_text(
            encoding="utf-8",
            errors="replace",
        )

        blocks: list[ParsedBlock] = []

        for line_number, line in enumerate(text.splitlines(), start=1):
            line = line.strip()

            if not line:
                continue

            blocks.append(
                ParsedBlock(
                    text=line,
                    location=SourceLocation(
                        line=line_number,
                    ),
                )
            )

        return ParsedDocument(
            filename=file_path.name,
            mime_type="text/plain",
            blocks=blocks,
        )