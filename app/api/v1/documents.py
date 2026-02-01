"""
Document endpoints for NetROS.
"""

import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.core.deps import get_current_active_user, require_role
from app.database import get_db
from app.models.document import Document, DocumentLink, LinkableEntity
from app.models.user import User, UserRole
from app.schemas.document import (
    DocumentResponse,
    DocumentUpdate,
    DocumentLinkCreate,
    DocumentLinkResponse,
    DocumentWithLinksResponse,
)

router = APIRouter()

# Upload directory - should be configurable via settings
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".txt", ".csv", ".json", ".xml",
    ".png", ".jpg", ".jpeg", ".gif",
    ".zip", ".tar", ".gz",
}

# Max file size (50 MB)
MAX_FILE_SIZE = 50 * 1024 * 1024


def validate_file_extension(filename: str) -> bool:
    """Validate file extension."""
    ext = Path(filename).suffix.lower()
    return ext in ALLOWED_EXTENSIONS


def generate_unique_filename(original_filename: str) -> str:
    """Generate a unique filename while preserving extension."""
    ext = Path(original_filename).suffix
    unique_id = uuid.uuid4().hex[:12]
    timestamp = datetime.utcnow().strftime("%Y%m%d")
    return f"{timestamp}_{unique_id}{ext}"


@router.get("/", response_model=list[DocumentResponse])
async def list_documents(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_active_user)],
    skip: int = 0,
    limit: int = 100,
    entity_type: LinkableEntity | None = None,
    entity_id: int | None = None,
) -> list[Document]:
    """List alle dokumenter, eventuelt filtrert på entitet."""
    if entity_type and entity_id:
        # Filter by entity link
        query = (
            select(Document)
            .join(DocumentLink)
            .where(
                DocumentLink.entity_type == entity_type,
                DocumentLink.entity_id == entity_id,
            )
        )
    else:
        query = select(Document)

    query = query.order_by(Document.uploaded_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_role(UserRole.ADMIN, UserRole.RISIKOANSVARLIG, UserRole.BRUKER)),
    ],
    description: str | None = None,
) -> Document:
    """Last opp et dokument."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filnavn mangler",
        )

    if not validate_file_extension(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ugyldig filtype. Tillatte typer: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Read file content
    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Filen er for stor. Maks størrelse: {MAX_FILE_SIZE // (1024*1024)} MB",
        )

    # Generate unique filename and save
    unique_filename = generate_unique_filename(file.filename)
    file_path = UPLOAD_DIR / unique_filename

    with open(file_path, "wb") as f:
        f.write(content)

    # Create document record
    document = Document(
        filename=file.filename,
        file_path=str(file_path),
        mime_type=file.content_type,
        file_size=len(content),
        description=description,
        uploaded_by_id=current_user.id,
        uploaded_at=datetime.utcnow(),
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)
    return document


@router.get("/statistics")
async def get_document_statistics(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """Hent statistikk for dokumenter."""
    # Total count
    total_result = await db.execute(select(func.count(Document.id)))
    total = total_result.scalar() or 0

    # Total size
    size_result = await db.execute(select(func.sum(Document.file_size)))
    total_size = size_result.scalar() or 0

    # By entity type
    type_result = await db.execute(
        select(DocumentLink.entity_type, func.count(DocumentLink.id))
        .group_by(DocumentLink.entity_type)
    )
    by_entity_type = {row[0].value: row[1] for row in type_result.all()}

    return {
        "total_documents": total,
        "total_size_bytes": total_size,
        "total_size_mb": round(total_size / (1024 * 1024), 2) if total_size else 0,
        "by_entity_type": by_entity_type,
    }


@router.get("/{document_id}", response_model=DocumentWithLinksResponse)
async def get_document(
    document_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_active_user)],
) -> Document:
    """Hent et dokument med metadata og koblinger."""
    result = await db.execute(
        select(Document)
        .options(selectinload(Document.links))
        .where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dokument ikke funnet",
        )

    return document


@router.get("/{document_id}/download")
async def download_document(
    document_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_active_user)],
) -> FileResponse:
    """Last ned et dokument."""
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dokument ikke funnet",
        )

    file_path = Path(document.file_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fil ikke funnet på disk",
        )

    return FileResponse(
        path=file_path,
        filename=document.filename,
        media_type=document.mime_type or "application/octet-stream",
    )


@router.patch("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: int,
    document_data: DocumentUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[
        User,
        Depends(require_role(UserRole.ADMIN, UserRole.RISIKOANSVARLIG, UserRole.BRUKER)),
    ],
) -> Document:
    """Oppdater dokumentmetadata."""
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dokument ikke funnet",
        )

    update_data = document_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(document, field, value)

    await db.commit()
    await db.refresh(document)
    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role(UserRole.ADMIN, UserRole.RISIKOANSVARLIG))],
) -> None:
    """Slett et dokument."""
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dokument ikke funnet",
        )

    # Delete file from disk
    file_path = Path(document.file_path)
    if file_path.exists():
        file_path.unlink()

    await db.delete(document)
    await db.commit()


# Document Links

@router.post("/{document_id}/link", response_model=DocumentLinkResponse, status_code=status.HTTP_201_CREATED)
async def link_document_to_entity(
    document_id: int,
    link_data: DocumentLinkCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[
        User,
        Depends(require_role(UserRole.ADMIN, UserRole.RISIKOANSVARLIG, UserRole.BRUKER)),
    ],
) -> DocumentLink:
    """Koble dokument til en entitet."""
    # Verify document exists
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dokument ikke funnet",
        )

    # Check if link already exists
    existing = await db.execute(
        select(DocumentLink)
        .where(
            DocumentLink.document_id == document_id,
            DocumentLink.entity_type == link_data.entity_type,
            DocumentLink.entity_id == link_data.entity_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Kobling finnes allerede",
        )

    link = DocumentLink(
        document_id=document_id,
        entity_type=link_data.entity_type,
        entity_id=link_data.entity_id,
        notes=link_data.notes,
    )
    db.add(link)
    await db.commit()
    await db.refresh(link)
    return link


@router.delete("/{document_id}/link/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unlink_document_from_entity(
    document_id: int,
    link_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[
        User,
        Depends(require_role(UserRole.ADMIN, UserRole.RISIKOANSVARLIG)),
    ],
) -> None:
    """Fjern kobling mellom dokument og entitet."""
    result = await db.execute(
        select(DocumentLink)
        .where(
            DocumentLink.id == link_id,
            DocumentLink.document_id == document_id,
        )
    )
    link = result.scalar_one_or_none()

    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kobling ikke funnet",
        )

    await db.delete(link)
    await db.commit()


# Entity-specific document endpoints

@router.get("/entity/{entity_type}/{entity_id}", response_model=list[DocumentResponse])
async def list_entity_documents(
    entity_type: LinkableEntity,
    entity_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_active_user)],
) -> list[Document]:
    """List alle dokumenter koblet til en spesifikk entitet."""
    query = (
        select(Document)
        .join(DocumentLink)
        .where(
            DocumentLink.entity_type == entity_type,
            DocumentLink.entity_id == entity_id,
        )
        .order_by(Document.uploaded_at.desc())
    )
    result = await db.execute(query)
    return list(result.scalars().all())
