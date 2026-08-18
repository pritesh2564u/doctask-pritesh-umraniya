from app.documents.models import ParsedBlock


MAX_CHUNK_CHARS = 2000


def create_chunks(
    blocks: list[ParsedBlock],
    max_chars: int = MAX_CHUNK_CHARS,
) -> list[dict]:
    chunks: list[dict] = []

    current_text: list[str] = []
    current_blocks: list[ParsedBlock] = []
    current_length = 0

    def flush() -> None:
        nonlocal current_text, current_blocks, current_length

        if not current_blocks:
            return

        first = current_blocks[0].location
        last = current_blocks[-1].location

        chunks.append(
            {
                "text": "\n".join(current_text),
                "start_page": first.page,
                "end_page": last.page,
                "start_paragraph": first.paragraph,
                "end_paragraph": last.paragraph,
                "start_line": first.line,
                "end_line": last.line,
            }
        )

        current_text = []
        current_blocks = []
        current_length = 0

    for block in blocks:
        text = block.text.strip()

        if not text:
            continue

        if current_length + len(text) > max_chars and current_blocks:
            flush()

        current_text.append(text)
        current_blocks.append(block)
        current_length += len(text)

    flush()

    for index, chunk in enumerate(chunks):
        chunk["chunk_index"] = index

    return chunks