"""
Dokumentmodell for vedlegg i NetROS.
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class LinkableEntity(str, Enum):
    """Entiteter som kan ha vedlegg."""

    RISK = "risk"
    REVIEW = "review"
    ASSET = "asset"
    PROJECT = "project"
    ACTION = "action"


class Document(Base, TimestampMixin):
    """Opplastet dokument/vedlegg."""

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(500))
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Opplastingsinfo
    uploaded_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
    )

    # Relationships
    uploaded_by: Mapped["User | None"] = relationship("User")
    links: Mapped[list["DocumentLink"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )


class DocumentLink(Base, TimestampMixin):
    """Kobling mellom Document og andre entiteter."""

    __tablename__ = "document_links"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), index=True)
    entity_type: Mapped[LinkableEntity]
    entity_id: Mapped[int] = mapped_column(Integer, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    document: Mapped["Document"] = relationship(back_populates="links")


# Import for type hints
from app.models.user import User
