import pytest
from sqlalchemy import text

from app.db.session import AsyncSessionLocal


@pytest.mark.asyncio
async def test_application_db_connection():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text("SELECT 1")
        )

        assert result.scalar() == 1