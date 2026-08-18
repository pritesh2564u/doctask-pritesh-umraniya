from dataclasses import dataclass, field


@dataclass
class SourceLocation:
    page: int | None = None
    paragraph: int | None = None
    section: str | None = None
    line: int | None = None


@dataclass
class ParsedBlock:
    text: str
    location: SourceLocation
    block_type: str = "text"


@dataclass
class ParsedDocument:
    filename: str
    mime_type: str
    blocks: list[ParsedBlock] = field(default_factory=list)