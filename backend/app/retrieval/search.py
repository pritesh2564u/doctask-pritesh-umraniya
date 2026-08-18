from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chunk import DocumentChunk
from app.models.document import Document
from app.retrieval.embeddings import EmbeddingProvider


async def search_chunks(
    db: AsyncSession,
    project_id: UUID,
    query: str,
    embedding_provider: EmbeddingProvider,
    limit: int = 5,
) -> list[DocumentChunk]:

    query_embedding = await embedding_provider.embed(query)

    distance = DocumentChunk.embedding.cosine_distance(
        query_embedding
    )

    result = await db.execute(
        select(DocumentChunk)
        .join(
            Document,
            Document.id == DocumentChunk.document_id,
        )
        .where(
            Document.project_id == project_id,
            DocumentChunk.embedding.is_not(None),
        )
        .order_by(distance)
        .limit(limit)
    )

    return list(result.scalars().all())