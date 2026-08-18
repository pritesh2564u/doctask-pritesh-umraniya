import pytest

from app.retrieval.embeddings import (
    DeterministicEmbeddingProvider,
)


@pytest.mark.asyncio
async def test_deterministic_embedding_is_reproducible():
    provider = DeterministicEmbeddingProvider(
        dimensions=8
    )

    first = await provider.embed(
        "Database integration is delayed."
    )

    second = await provider.embed(
        "Database integration is delayed."
    )

    assert first == second
    assert len(first) == 8


@pytest.mark.asyncio
async def test_different_text_produces_different_embedding():
    provider = DeterministicEmbeddingProvider(
        dimensions=8
    )

    first = await provider.embed("API development")
    second = await provider.embed("Frontend development")

    assert first != second


@pytest.mark.asyncio
async def test_embedding_is_normalized():
    provider = DeterministicEmbeddingProvider(
        dimensions=8
    )

    vector = await provider.embed("Project Alpha")

    magnitude = sum(
        value * value
        for value in vector
    ) ** 0.5

    assert magnitude == pytest.approx(1.0)