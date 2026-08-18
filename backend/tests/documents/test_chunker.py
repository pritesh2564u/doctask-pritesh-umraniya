from app.documents.chunker import create_chunks
from app.documents.models import ParsedBlock, SourceLocation


def test_create_chunks_preserves_line_locations():
    blocks = [
        ParsedBlock(
            text="Project Alpha",
            location=SourceLocation(line=1),
        ),
        ParsedBlock(
            text="API development is completed.",
            location=SourceLocation(line=2),
        ),
        ParsedBlock(
            text="Frontend development is in progress.",
            location=SourceLocation(line=3),
        ),
    ]

    chunks = create_chunks(blocks, max_chars=2000)

    assert len(chunks) == 1
    assert chunks[0]["chunk_index"] == 0
    assert chunks[0]["start_line"] == 1
    assert chunks[0]["end_line"] == 3
    assert "API development is completed." in chunks[0]["text"]


def test_large_content_creates_multiple_chunks():
    blocks = [
        ParsedBlock(
            text="A" * 100,
            location=SourceLocation(line=1),
        ),
        ParsedBlock(
            text="B" * 100,
            location=SourceLocation(line=2),
        ),
        ParsedBlock(
            text="C" * 100,
            location=SourceLocation(line=3),
        ),
    ]

    chunks = create_chunks(blocks, max_chars=150)

    assert len(chunks) == 3
    assert chunks[0]["chunk_index"] == 0
    assert chunks[1]["chunk_index"] == 1
    assert chunks[2]["chunk_index"] == 2