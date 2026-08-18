from abc import ABC, abstractmethod
from pathlib import Path

from app.documents.models import ParsedDocument


class DocumentParser(ABC):

    @abstractmethod
    def parse(self, file_path: Path) -> ParsedDocument:
        """Parse a document into the normalized representation."""
        raise NotImplementedError