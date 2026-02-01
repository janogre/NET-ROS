"""
InformationAsset endpoints for NetROS.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user, require_role
from app.database import get_db
from app.models.information_asset import InformationAsset, Classification
from app.models.user import User, UserRole
from app.schemas.information_asset import (
    InformationAssetCreate,
    InformationAssetUpdate,
    InformationAssetResponse,
    InformationAssetListResponse,
)

router = APIRouter()


@router.get("/", response_model=list[InformationAssetResponse])
async def list_information_assets(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_active_user)],
    skip: int = 0,
    limit: int = 100,
    classification: Classification | None = None,
    owner_department_id: int | None = None,
) -> list[InformationAsset]:
    """List alle informasjonsverdier."""
    query = select(InformationAsset)

    if classification:
        query = query.where(InformationAsset.classification == classification)

    if owner_department_id:
        query = query.where(InformationAsset.owner_department_id == owner_department_id)

    query = query.order_by(InformationAsset.name).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("/", response_model=InformationAssetResponse, status_code=status.HTTP_201_CREATED)
async def create_information_asset(
    asset_data: InformationAssetCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[
        User,
        Depends(require_role(UserRole.ADMIN, UserRole.RISIKOANSVARLIG, UserRole.BRUKER)),
    ],
) -> InformationAsset:
    """Opprett ny informasjonsverdi."""
    asset = InformationAsset(
        name=asset_data.name,
        description=asset_data.description,
        classification=asset_data.classification,
        owner_department_id=asset_data.owner_department_id,
    )
    # Set data_types using the property setter
    asset.data_types = asset_data.data_types

    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    return asset


@router.get("/statistics")
async def get_information_asset_statistics(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """Hent statistikk for informasjonsverdier."""
    # Total count
    total_result = await db.execute(select(func.count(InformationAsset.id)))
    total = total_result.scalar() or 0

    # By classification
    class_result = await db.execute(
        select(InformationAsset.classification, func.count(InformationAsset.id))
        .group_by(InformationAsset.classification)
    )
    by_classification = {row[0].value: row[1] for row in class_result.all()}

    return {
        "total": total,
        "by_classification": by_classification,
    }


@router.get("/{asset_id}", response_model=InformationAssetResponse)
async def get_information_asset(
    asset_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_active_user)],
) -> InformationAsset:
    """Hent en informasjonsverdi."""
    result = await db.execute(
        select(InformationAsset).where(InformationAsset.id == asset_id)
    )
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Informasjonsverdi ikke funnet",
        )

    return asset


@router.patch("/{asset_id}", response_model=InformationAssetResponse)
async def update_information_asset(
    asset_id: int,
    asset_data: InformationAssetUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[
        User,
        Depends(require_role(UserRole.ADMIN, UserRole.RISIKOANSVARLIG, UserRole.BRUKER)),
    ],
) -> InformationAsset:
    """Oppdater en informasjonsverdi."""
    result = await db.execute(
        select(InformationAsset).where(InformationAsset.id == asset_id)
    )
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Informasjonsverdi ikke funnet",
        )

    update_data = asset_data.model_dump(exclude_unset=True)

    # Handle data_types separately due to property setter
    if "data_types" in update_data:
        asset.data_types = update_data.pop("data_types")

    for field, value in update_data.items():
        setattr(asset, field, value)

    await db.commit()
    await db.refresh(asset)
    return asset


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_information_asset(
    asset_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role(UserRole.ADMIN, UserRole.RISIKOANSVARLIG))],
) -> None:
    """Slett en informasjonsverdi."""
    result = await db.execute(
        select(InformationAsset).where(InformationAsset.id == asset_id)
    )
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Informasjonsverdi ikke funnet",
        )

    await db.delete(asset)
    await db.commit()


@router.get("/{asset_id}/risks")
async def get_information_asset_risks(
    asset_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_active_user)],
) -> list[dict]:
    """Hent risikoer knyttet til en informasjonsverdi."""
    from app.models.risk import Risk, InformationAssetRisk

    result = await db.execute(
        select(InformationAsset).where(InformationAsset.id == asset_id)
    )
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Informasjonsverdi ikke funnet",
        )

    risks_result = await db.execute(
        select(Risk)
        .join(InformationAssetRisk)
        .where(InformationAssetRisk.information_asset_id == asset_id)
    )
    risks = risks_result.scalars().all()

    return [
        {
            "id": r.id,
            "title": r.title,
            "risk_score": r.risk_score,
            "risk_level": r.risk_level,
            "status": r.status.value,
        }
        for r in risks
    ]


@router.post("/{asset_id}/risks/{risk_id}", status_code=status.HTTP_201_CREATED)
async def link_information_asset_to_risk(
    asset_id: int,
    risk_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[
        User,
        Depends(require_role(UserRole.ADMIN, UserRole.RISIKOANSVARLIG)),
    ],
    notes: str | None = None,
) -> dict:
    """Koble informasjonsverdi til risiko."""
    from app.models.risk import Risk, InformationAssetRisk

    # Verify asset exists
    result = await db.execute(
        select(InformationAsset).where(InformationAsset.id == asset_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Informasjonsverdi ikke funnet",
        )

    # Verify risk exists
    result = await db.execute(select(Risk).where(Risk.id == risk_id))
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Risiko ikke funnet",
        )

    # Check if link already exists
    existing = await db.execute(
        select(InformationAssetRisk)
        .where(
            InformationAssetRisk.information_asset_id == asset_id,
            InformationAssetRisk.risk_id == risk_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Kobling finnes allerede",
        )

    link = InformationAssetRisk(
        information_asset_id=asset_id,
        risk_id=risk_id,
        notes=notes,
    )
    db.add(link)
    await db.commit()

    return {"message": "Kobling opprettet", "information_asset_id": asset_id, "risk_id": risk_id}


@router.delete("/{asset_id}/risks/{risk_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unlink_information_asset_from_risk(
    asset_id: int,
    risk_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[
        User,
        Depends(require_role(UserRole.ADMIN, UserRole.RISIKOANSVARLIG)),
    ],
) -> None:
    """Fjern kobling mellom informasjonsverdi og risiko."""
    from app.models.risk import InformationAssetRisk

    result = await db.execute(
        select(InformationAssetRisk)
        .where(
            InformationAssetRisk.information_asset_id == asset_id,
            InformationAssetRisk.risk_id == risk_id,
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
