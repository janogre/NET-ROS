"""
Risk endpoints for NetROS.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_active_user, require_role
from app.database import get_db
from app.models.risk import Risk
from app.models.user import User, UserRole
from app.schemas.risk import RiskCreate, RiskUpdate, RiskResponse, RiskMatrix
from app.services.risk_service import RiskService

router = APIRouter()


@router.get("/", response_model=list[RiskResponse])
async def list_risks(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_active_user)],
    skip: int = 0,
    limit: int = 100,
    project_id: int | None = None,
    status_filter: str | None = None,
    likelihood: int | None = None,
    consequence: int | None = None,
    target_likelihood: int | None = None,
    target_consequence: int | None = None,
) -> list[Risk]:
    """List alle risikoer med valgfrie filtre."""
    query = select(Risk).options(selectinload(Risk.owner), selectinload(Risk.project))

    if project_id:
        query = query.where(Risk.project_id == project_id)
    if status_filter:
        query = query.where(Risk.status == status_filter)
    if likelihood:
        query = query.where(Risk.likelihood == likelihood)
    if consequence:
        query = query.where(Risk.consequence == consequence)
    if target_likelihood:
        query = query.where(Risk.target_likelihood == target_likelihood)
    if target_consequence:
        query = query.where(Risk.target_consequence == target_consequence)

    query = query.order_by(Risk.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("/", response_model=RiskResponse, status_code=status.HTTP_201_CREATED)
async def create_risk(
    risk_data: RiskCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(
            require_role(UserRole.ADMIN, UserRole.RISIKOANSVARLIG, UserRole.BRUKER)
        ),
    ],
) -> Risk:
    """Opprett ny risiko."""
    # Set owner to current user if not specified
    if not risk_data.owner_id:
        risk_data.owner_id = current_user.id

    risk_service = RiskService(db)
    return await risk_service.create_risk(risk_data)


@router.get("/matrix", response_model=RiskMatrix)
async def get_risk_matrix(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_active_user)],
    project_id: int | None = None,
) -> RiskMatrix:
    """Hent risikomatrise."""
    risk_service = RiskService(db)
    return await risk_service.get_risk_matrix(project_id)


@router.get("/matrix/target", response_model=RiskMatrix)
async def get_target_risk_matrix(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_active_user)],
    project_id: int | None = None,
) -> RiskMatrix:
    """Hent mål-risikomatrise (etter tiltak)."""
    risk_service = RiskService(db)
    return await risk_service.get_target_risk_matrix(project_id)


@router.get("/{risk_id}", response_model=RiskResponse)
async def get_risk(
    risk_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_active_user)],
) -> Risk:
    """Hent en risiko."""
    result = await db.execute(
        select(Risk).options(selectinload(Risk.owner), selectinload(Risk.project)).where(Risk.id == risk_id)
    )
    risk = result.scalar_one_or_none()

    if not risk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Risiko ikke funnet",
        )

    return risk


@router.patch("/{risk_id}", response_model=RiskResponse)
async def update_risk(
    risk_id: int,
    risk_data: RiskUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[
        User,
        Depends(
            require_role(UserRole.ADMIN, UserRole.RISIKOANSVARLIG, UserRole.BRUKER)
        ),
    ],
) -> Risk:
    """Oppdater en risiko."""
    risk_service = RiskService(db)
    risk = await risk_service.update_risk(risk_id, risk_data)

    if not risk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Risiko ikke funnet",
        )

    return risk


@router.delete("/{risk_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_risk(
    risk_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role(UserRole.ADMIN, UserRole.RISIKOANSVARLIG))],
) -> None:
    """Slett en risiko."""
    result = await db.execute(select(Risk).where(Risk.id == risk_id))
    risk = result.scalar_one_or_none()

    if not risk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Risiko ikke funnet",
        )

    await db.delete(risk)
    await db.commit()


@router.get("/{risk_id}/assets")
async def get_risk_assets(
    risk_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_active_user)],
) -> list[dict]:
    """Hent assets knyttet til en risiko."""
    from app.models.asset import Asset
    from app.models.risk import AssetRisk

    result = await db.execute(select(Risk).where(Risk.id == risk_id))
    risk = result.scalar_one_or_none()

    if not risk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Risiko ikke funnet",
        )

    assets_result = await db.execute(
        select(Asset).join(AssetRisk).where(AssetRisk.risk_id == risk_id)
    )
    assets = assets_result.scalars().all()

    return [
        {
            "id": a.id,
            "name": a.name,
            "category": a.category.value,
            "criticality": a.criticality,
            "criticality_label": a.criticality_label,
        }
        for a in assets
    ]


@router.post("/{risk_id}/assets/{asset_id}", status_code=status.HTTP_201_CREATED)
async def add_asset_to_risk(
    risk_id: int,
    asset_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[
        User,
        Depends(
            require_role(UserRole.ADMIN, UserRole.RISIKOANSVARLIG, UserRole.BRUKER)
        ),
    ],
) -> dict:
    """Koble en asset til en risiko."""
    from app.models.asset import Asset
    from app.models.risk import AssetRisk

    # Verify risk exists
    result = await db.execute(select(Risk).where(Risk.id == risk_id))
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Risiko ikke funnet",
        )

    # Verify asset exists
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset ikke funnet",
        )

    # Check if already linked
    result = await db.execute(
        select(AssetRisk).where(
            AssetRisk.risk_id == risk_id, AssetRisk.asset_id == asset_id
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Asset er allerede knyttet til denne risikoen",
        )

    asset_risk = AssetRisk(risk_id=risk_id, asset_id=asset_id)
    db.add(asset_risk)
    await db.commit()

    return {"message": "Asset koblet til risiko"}


@router.delete("/{risk_id}/assets/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_asset_from_risk(
    risk_id: int,
    asset_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[
        User,
        Depends(
            require_role(UserRole.ADMIN, UserRole.RISIKOANSVARLIG, UserRole.BRUKER)
        ),
    ],
) -> None:
    """Fjern kobling mellom asset og risiko."""
    from app.models.risk import AssetRisk

    result = await db.execute(
        select(AssetRisk).where(
            AssetRisk.risk_id == risk_id, AssetRisk.asset_id == asset_id
        )
    )
    asset_risk = result.scalar_one_or_none()

    if not asset_risk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kobling ikke funnet",
        )

    await db.delete(asset_risk)
    await db.commit()


# NSM Mapping endpoints

@router.get("/{risk_id}/nsm-mappings")
async def get_risk_nsm_mappings(
    risk_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_active_user)],
) -> list[dict]:
    """Hent NSM-prinsipper koblet til en risiko."""
    from app.models.risk import NSMMapping
    from app.models.nsm import NSMPrinciple

    result = await db.execute(select(Risk).where(Risk.id == risk_id))
    risk = result.scalar_one_or_none()

    if not risk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Risiko ikke funnet",
        )

    mappings_result = await db.execute(
        select(NSMMapping, NSMPrinciple)
        .join(NSMPrinciple)
        .where(NSMMapping.risk_id == risk_id)
        .order_by(NSMPrinciple.sort_order)
    )
    mappings = mappings_result.all()

    return [
        {
            "mapping_id": m.NSMMapping.id,
            "principle_id": p.id,
            "code": p.code,
            "title": p.title,
            "category": p.category.value,
            "notes": m.NSMMapping.notes,
        }
        for m, p in [(row[0], row[1]) for row in mappings]
    ]


@router.post("/{risk_id}/nsm-mappings/{principle_id}", status_code=status.HTTP_201_CREATED)
async def add_nsm_mapping_to_risk(
    risk_id: int,
    principle_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[
        User,
        Depends(require_role(UserRole.ADMIN, UserRole.RISIKOANSVARLIG)),
    ],
    notes: str | None = None,
) -> dict:
    """Koble et NSM-prinsipp til en risiko."""
    from app.models.risk import NSMMapping
    from app.models.nsm import NSMPrinciple

    # Verify risk exists
    result = await db.execute(select(Risk).where(Risk.id == risk_id))
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Risiko ikke funnet",
        )

    # Verify principle exists
    result = await db.execute(select(NSMPrinciple).where(NSMPrinciple.id == principle_id))
    principle = result.scalar_one_or_none()
    if not principle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="NSM-prinsipp ikke funnet",
        )

    # Check if already linked
    result = await db.execute(
        select(NSMMapping).where(
            NSMMapping.risk_id == risk_id,
            NSMMapping.nsm_principle_id == principle_id,
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="NSM-prinsipp er allerede koblet til denne risikoen",
        )

    mapping = NSMMapping(
        risk_id=risk_id,
        nsm_principle_id=principle_id,
        notes=notes,
    )
    db.add(mapping)
    await db.commit()

    return {
        "message": "NSM-prinsipp koblet til risiko",
        "principle_code": principle.code,
        "principle_title": principle.title,
    }


@router.delete("/{risk_id}/nsm-mappings/{principle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_nsm_mapping_from_risk(
    risk_id: int,
    principle_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[
        User,
        Depends(require_role(UserRole.ADMIN, UserRole.RISIKOANSVARLIG)),
    ],
) -> None:
    """Fjern kobling mellom NSM-prinsipp og risiko."""
    from app.models.risk import NSMMapping

    result = await db.execute(
        select(NSMMapping).where(
            NSMMapping.risk_id == risk_id,
            NSMMapping.nsm_principle_id == principle_id,
        )
    )
    mapping = result.scalar_one_or_none()

    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="NSM-mapping ikke funnet",
        )

    await db.delete(mapping)
    await db.commit()


@router.get("/nsm-principles/all")
async def list_all_nsm_principles(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_active_user)],
) -> list[dict]:
    """List alle tilgjengelige NSM-prinsipper."""
    from app.models.nsm import NSMPrinciple

    result = await db.execute(
        select(NSMPrinciple).order_by(NSMPrinciple.sort_order)
    )
    principles = result.scalars().all()

    return [
        {
            "id": p.id,
            "code": p.code,
            "title": p.title,
            "category": p.category.value,
            "description": p.description,
        }
        for p in principles
    ]
