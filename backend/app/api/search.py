from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.retrieval.embeddings import (
    DeterministicEmbeddingProvider,
)
from app.retrieval.search import search_chunks

router = APIRouter(
    prefix="/projects",
    tags=["search"],
)

embedding_provider = DeterministicEmbeddingProvider(
    dimensions=1536
)


@router.get("/{project_id}/search")
async def search_project(
    project_id: UUID,
    q: str = Query(..., min_length=1),
    limit: int = Query(
        default=5,
        ge=1,
        le=20,
    ),
    db: AsyncSession = Depends(get_db),
):
    chunks = await search_chunks(
        db=db,
        project_id=project_id,
        query=q,
        embedding_provider=embedding_provider,
        limit=limit,
    )

    return {
        "query": q,
        "results": [
            {
                "chunk_id": str(chunk.id),
                "document_id": str(chunk.document_id),
                "chunk_index": chunk.chunk_index,
                "text": chunk.text,
                "source": {
                    "start_page": chunk.start_page,
                    "end_page": chunk.end_page,
                    "start_paragraph": chunk.start_paragraph,
                    "end_paragraph": chunk.end_paragraph,
                    "start_line": chunk.start_line,
                    "end_line": chunk.end_line,
                },
            }
            for chunk in chunks
        ],
    }