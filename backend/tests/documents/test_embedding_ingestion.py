from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from app.documents.chunker import create_chunks
from app.documents.models import ParsedBlock, SourceLocation
from app.retrieval.embeddings import DeterministicEmbeddingProvider


@pytest.mark.asyncio
async def test_embedding_provider_generates_embedding_for_chunks():
    blocks = [
        ParsedBlock(
            text="Project Alpha API is complete.",
            location=SourceLocation(line=1),
        ),
        ParsedBlock(
            text="Frontend development is in progress.",
            location=SourceLocation(line=2),
        ),
    ]

    chunks = create_chunks(blocks)

    provider = DeterministicEmbeddingProvider(
        dimensions=1536
    )

    embeddings = await provider.embed_many(
        [chunk["text"] for chunk in chunks]
    )

    assert len(embeddings) == len(chunks)

    for embedding in embeddings:
        assert len(embedding) == 1536
        assert all(
            isinstance(value, float)
            for value in embedding
        )