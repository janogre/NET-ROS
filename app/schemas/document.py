"""
Pydantic schemas for Document.
"""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.document import LinkableEntity


class DocumentBase(BaseModel):
    """Base schema for Document."""

    filename: str = Field(..., min_length=1, max_length=255)
    description: str | None = None


class DocumentCreate(DocumentBase):
    """Schema for creating a document (metadata only, file uploaded separately)."""

    pass


class DocumentUpdate(BaseModel):
    """Schema for updating a document."""

    description: str | None = None


class DocumentResponse(DocumentBase):
    """Schema for document response."""

    id: int
    file_path: str
    mime_type: str | None = None
    file_size: int | None = None
    uploaded_by_id: int | None = None
    uploaded_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentLinkCreate(BaseModel):
    """Schema for linking a document to an entity."""

    document_id: int
    entity_type: LinkableEntity
    entity_id: int
    notes: str | None = None


class DocumentLinkResponse(BaseModel):
    """Schema for document link response."""

    id: int
    document_id: int
    entity_type: LinkableEntity
    entity_id: int
    notes: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentWithLinksResponse(DocumentResponse):
    """Schema for document with its links."""

    links: list[DocumentLinkResponse] = []
