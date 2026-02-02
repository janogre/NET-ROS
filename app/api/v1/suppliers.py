"""
Supplier endpoints for NetROS.
"""

from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_active_user, require_role
from app.database import get_db
from app.models.supplier import Supplier, AssetSupplier, SupplierType
from app.models.user import User, UserRole
from app.schemas.supplier import SupplierCreate, SupplierUpdate, SupplierResponse
from app.services.audit_service import AuditService

router = APIRouter()


@router.get("/", response_model=list[SupplierResponse])
async def list_suppliers(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_active_user)],
    skip: int = 0,
    limit: int = 100,
    supplier_type: SupplierType | None = None,
    criticality_min: int | None = Query(None, ge=1, le=5),
    expiring_within_days: int | None = Query(None, ge=0, description="Filtrer leverandører med kontrakt som utløper innen X dager"),
) -> list[Supplier]:
    """List alle leverandører."""
    query = select(Supplier)

    if supplier_type:
        query = query.where(Supplier.supplier_type == supplier_type)

    if criticality_min:
        query = query.where(Supplier.criticality >= criticality_min)

    if expiring_within_days is not None:
        expiry_date = date.today() + timedelta(days=expiring_within_days)
        query = query.where(
            Supplier.contract_expiry.isnot(None),
            Supplier.contract_expiry <= expiry_date,
            Supplier.contract_expiry >= date.today(),
        )

    query = query.order_by(Supplier.name).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("/", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
async def create_supplier(
    supplier_data: SupplierCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_role(UserRole.ADMIN, UserRole.RISIKOANSVARLIG)),
    ],
) -> Supplier:
    """Opprett ny leverandør."""
    supplier = Supplier(
        name=supplier_data.name,
        description=supplier_data.description,
        supplier_type=supplier_data.supplier_type,
        criticality=supplier_data.criticality,
        contact_info=supplier_data.contact_info,
        contract_reference=supplier_data.contract_reference,
        contract_expiry=supplier_data.contract_expiry,
    )
    db.add(supplier)
    await db.flush()

    # Audit log
    audit_service = AuditService(db)
    await audit_service.log_create(
        entity_type="supplier",
        entity_id=supplier.id,
        user=current_user,
        values={
            "name": supplier.name,
            "supplier_type": supplier.supplier_type.value,
            "criticality": supplier.criticality,
        },
    )

    await db.commit()
    await db.refresh(supplier)
    return supplier


@router.get("/expiring", response_model=list[SupplierResponse])
async def list_expiring_contracts(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_active_user)],
    days: int = Query(90, ge=0, description="Antall dager fremover å se etter utløpende kontrakter"),
) -> list[Supplier]:
    """List leverandører med kontrakter som utløper snart."""
    expiry_date = date.today() + timedelta(days=days)
    query = (
        select(Supplier)
        .where(
            Supplier.contract_expiry.isnot(None),
            Supplier.contract_expiry <= expiry_date,
            Supplier.contract_expiry >= date.today(),
        )
        .order_by(Supplier.contract_expiry)
    )
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/statistics")
async def get_supplier_statistics(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """Hent statistikk for leverandører."""
    # Total count
    total_result = await db.execute(select(func.count(Supplier.id)))
    total = total_result.scalar() or 0

    # By type
    type_result = await db.execute(
        select(Supplier.supplier_type, func.count(Supplier.id))
        .group_by(Supplier.supplier_type)
    )
    by_type = {row[0].value: row[1] for row in type_result.all()}

    # By criticality
    crit_result = await db.execute(
        select(Supplier.criticality, func.count(Supplier.id))
        .group_by(Supplier.criticality)
    )
    by_criticality = {row[0]: row[1] for row in crit_result.all()}

    # Expiring contracts (30, 60, 90 days)
    expiring = {}
    for days in [30, 60, 90]:
        expiry_date = date.today() + timedelta(days=days)
        exp_result = await db.execute(
            select(func.count(Supplier.id))
            .where(
                Supplier.contract_expiry.isnot(None),
                Supplier.contract_expiry <= expiry_date,
                Supplier.contract_expiry >= date.today(),
            )
        )
        expiring[f"within_{days}_days"] = exp_result.scalar() or 0

    return {
        "total": total,
        "by_type": by_type,
        "by_criticality": by_criticality,
        "expiring_contracts": expiring,
    }


@router.get("/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(
    supplier_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_active_user)],
) -> Supplier:
    """Hent en leverandør."""
    result = await db.execute(
        select(Supplier).where(Supplier.id == supplier_id)
    )
    supplier = result.scalar_one_or_none()

    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leverandør ikke funnet",
        )

    return supplier


@router.patch("/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(
    supplier_id: int,
    supplier_data: SupplierUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_role(UserRole.ADMIN, UserRole.RISIKOANSVARLIG)),
    ],
) -> Supplier:
    """Oppdater en leverandør."""
    result = await db.execute(
        select(Supplier).where(Supplier.id == supplier_id)
    )
    supplier = result.scalar_one_or_none()

    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leverandør ikke funnet",
        )

    # Save old values for audit
    old_values = {
        "name": supplier.name,
        "criticality": supplier.criticality,
        "contract_expiry": supplier.contract_expiry.isoformat() if supplier.contract_expiry else None,
    }

    update_data = supplier_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(supplier, field, value)

    # Audit log
    new_values = {
        "name": supplier.name,
        "criticality": supplier.criticality,
        "contract_expiry": supplier.contract_expiry.isoformat() if supplier.contract_expiry else None,
    }
    audit_service = AuditService(db)
    await audit_service.log_update(
        entity_type="supplier",
        entity_id=supplier.id,
        user=current_user,
        old_values=old_values,
        new_values=new_values,
    )

    await db.commit()
    await db.refresh(supplier)
    return supplier


@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_supplier(
    supplier_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
) -> None:
    """Slett en leverandør."""
    result = await db.execute(
        select(Supplier).where(Supplier.id == supplier_id)
    )
    supplier = result.scalar_one_or_none()

    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leverandør ikke funnet",
        )

    # Audit log before delete
    audit_service = AuditService(db)
    await audit_service.log_delete(
        entity_type="supplier",
        entity_id=supplier.id,
        user=current_user,
        values={"name": supplier.name, "criticality": supplier.criticality},
    )

    await db.delete(supplier)
    await db.commit()


@router.get("/{supplier_id}/assets")
async def get_supplier_assets(
    supplier_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_active_user)],
) -> list[dict]:
    """Hent assets knyttet til en leverandør."""
    from app.models.asset import Asset

    result = await db.execute(
        select(Supplier).where(Supplier.id == supplier_id)
    )
    supplier = result.scalar_one_or_none()

    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leverandør ikke funnet",
        )

    assets_result = await db.execute(
        select(Asset)
        .join(AssetSupplier)
        .where(AssetSupplier.supplier_id == supplier_id)
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


@router.post("/{supplier_id}/assets/{asset_id}", status_code=status.HTTP_201_CREATED)
async def link_supplier_to_asset(
    supplier_id: int,
    asset_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[
        User,
        Depends(require_role(UserRole.ADMIN, UserRole.RISIKOANSVARLIG)),
    ],
    notes: str | None = None,
) -> dict:
    """Koble leverandør til asset."""
    from app.models.asset import Asset

    # Verify supplier exists
    result = await db.execute(
        select(Supplier).where(Supplier.id == supplier_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leverandør ikke funnet",
        )

    # Verify asset exists
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset ikke funnet",
        )

    # Check if link already exists
    existing = await db.execute(
        select(AssetSupplier)
        .where(
            AssetSupplier.supplier_id == supplier_id,
            AssetSupplier.asset_id == asset_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Kobling finnes allerede",
        )

    link = AssetSupplier(
        supplier_id=supplier_id,
        asset_id=asset_id,
        notes=notes,
    )
    db.add(link)
    await db.commit()

    return {"message": "Kobling opprettet", "supplier_id": supplier_id, "asset_id": asset_id}


@router.delete("/{supplier_id}/assets/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unlink_supplier_from_asset(
    supplier_id: int,
    asset_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[
        User,
        Depends(require_role(UserRole.ADMIN, UserRole.RISIKOANSVARLIG)),
    ],
) -> None:
    """Fjern kobling mellom leverandør og asset."""
    result = await db.execute(
        select(AssetSupplier)
        .where(
            AssetSupplier.supplier_id == supplier_id,
            AssetSupplier.asset_id == asset_id,
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
