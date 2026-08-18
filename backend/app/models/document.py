from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    filename: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    mime_type: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    storage_path: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )

    content_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    document_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )