from pathlib import Path

from app.documents.parser import DocumentParser
from app.documents.parsers.docx import DOCXParser
from app.documents.parsers.pdf import PDFParser
from app.documents.parsers.text import TextParser


class ParserRegistry:

    def __init__(self) -> None:
        self._parsers: dict[str, DocumentParser] = {}

    def register(
        self,
        extension: str,
        parser: DocumentParser,
    ) -> None:
        extension = extension.lower()

        if not extension.startswith("."):
            extension = f".{extension}"

        self._parsers[extension] = parser

    def get_parser(self, file_path: Path) -> DocumentParser:
        extension = file_path.suffix.lower()

        parser = self._parsers.get(extension)

        if parser is None:
            raise ValueError(
                f"Unsupported document format: {extension}"
            )

        return parser


def create_default_registry() -> ParserRegistry:
    registry = ParserRegistry()

    registry.register(".pdf", PDFParser())
    registry.register(".docx", DOCXParser())
    registry.register(".txt", TextParser())

    return registry