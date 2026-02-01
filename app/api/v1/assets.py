"""
Asset endpoints for NetROS.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user, require_role
from app.database import get_db
from app.models.asset import Asset
from app.models.user import User, UserRole
from app.schemas.asset import AssetCreate, AssetUpdate, AssetResponse

router = APIRouter()


@router.get("/", response_model=list[AssetResponse])
async def list_assets(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_active_user)],
    skip: int = 0,
    limit: int = 100,
    category: str | None = None,
) -> list[Asset]:
    """List alle assets."""
    query = select(Asset)

    if category:
        query = query.where(Asset.category == category)

    query = query.order_by(Asset.name).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("/", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
async def create_asset(
    asset_data: AssetCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[
        User,
        Depends(
            require_role(UserRole.ADMIN, UserRole.RISIKOANSVARLIG, UserRole.BRUKER)
        ),
    ],
) -> Asset:
    """Opprett ny asset."""
    asset = Asset(
        name=asset_data.name,
        description=asset_data.description,
        asset_type=asset_data.asset_type,
        category=asset_data.category,
        criticality=asset_data.criticality,
        location=asset_data.location,
        ip_address=asset_data.ip_address,
        serial_number=asset_data.serial_number,
        manufacturer=asset_data.manufacturer,
        model=asset_data.model,
        parent_id=asset_data.parent_id,
        owner_department_id=asset_data.owner_department_id,
        is_manual=True,
    )
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    return asset


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_active_user)],
) -> Asset:
    """Hent en asset."""
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset ikke funnet",
        )

    return asset


@router.patch("/{asset_id}", response_model=AssetResponse)
async def update_asset(
    asset_id: int,
    asset_data: AssetUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[
        User,
        Depends(
            require_role(UserRole.ADMIN, UserRole.RISIKOANSVARLIG, UserRole.BRUKER)
        ),
    ],
) -> Asset:
    """Oppdater en asset."""
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset ikke funnet",
        )

    update_data = asset_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(asset, field, value)

    await db.commit()
    await db.refresh(asset)
    return asset


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset(
    asset_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role(UserRole.ADMIN, UserRole.RISIKOANSVARLIG))],
) -> None:
    """Slett en asset."""
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset ikke funnet",
        )

    await db.delete(asset)
    await db.commit()


@router.get("/{asset_id}/risks")
async def get_asset_risks(
    asset_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_active_user)],
) -> list[dict]:
    """Hent risikoer knyttet til en asset."""
    from app.models.risk import Risk, AssetRisk

    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset ikke funnet",
        )

    risks_result = await db.execute(
        select(Risk)
        .join(AssetRisk)
        .where(AssetRisk.asset_id == asset_id)
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
