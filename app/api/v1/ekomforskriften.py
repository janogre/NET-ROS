"""
Ekomforskriften endpoints for NetROS.
Compliance tracking for Norwegian telecom regulations.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_active_user, require_role
from app.database import get_db
from app.models.ekomforskriften import (
    EkomPrinciple,
    EkomMapping,
    EkomActionMapping,
    EkomCategory,
    EkomParagraph,
)
from app.models.risk import Risk
from app.models.action import Action
from app.models.user import User, UserRole
from app.schemas.ekomforskriften import (
    EkomPrincipleCreate,
    EkomPrincipleUpdate,
    EkomPrincipleResponse,
    EkomMappingCreate,
    EkomMappingUpdate,
    EkomMappingResponse,
    EkomActionMappingCreate,
    EkomActionMappingResponse,
    EkomComplianceSummary,
    EkomComplianceByCategory,
)

router = APIRouter()


# Principles CRUD

@router.get("/principles", response_model=list[EkomPrincipleResponse])
async def list_ekom_principles(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_active_user)],
    category: EkomCategory | None = None,
    paragraph: EkomParagraph | None = None,
) -> list[EkomPrinciple]:
    """List alle Ekomforskriften-prinsipper."""
    query = select(EkomPrinciple)

    if category:
        query = query.where(EkomPrinciple.category == category)

    if paragraph:
        query = query.where(EkomPrinciple.paragraph == paragraph)

    query = query.order_by(EkomPrinciple.sort_order, EkomPrinciple.code)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("/principles", response_model=EkomPrincipleResponse, status_code=status.HTTP_201_CREATED)
async def create_ekom_principle(
    principle_data: EkomPrincipleCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role(UserRole.ADMIN))],
) -> EkomPrinciple:
    """Opprett nytt Ekomforskriften-prinsipp."""
    # Check if code already exists
    existing = await db.execute(
        select(EkomPrinciple).where(EkomPrinciple.code == principle_data.code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Prinsipp med kode {principle_data.code} finnes allerede",
        )

    principle = EkomPrinciple(**principle_data.model_dump())
    db.add(principle)
    await db.commit()
    await db.refresh(principle)
    return principle


@router.get("/principles/{principle_id}", response_model=EkomPrincipleResponse)
async def get_ekom_principle(
    principle_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_active_user)],
) -> EkomPrinciple:
    """Hent et Ekomforskriften-prinsipp."""
    result = await db.execute(
        select(EkomPrinciple).where(EkomPrinciple.id == principle_id)
    )
    principle = result.scalar_one_or_none()

    if not principle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prinsipp ikke funnet",
        )

    return principle


@router.patch("/principles/{principle_id}", response_model=EkomPrincipleResponse)
async def update_ekom_principle(
    principle_id: int,
    principle_data: EkomPrincipleUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role(UserRole.ADMIN))],
) -> EkomPrinciple:
    """Oppdater et Ekomforskriften-prinsipp."""
    result = await db.execute(
        select(EkomPrinciple).where(EkomPrinciple.id == principle_id)
    )
    principle = result.scalar_one_or_none()

    if not principle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prinsipp ikke funnet",
        )

    update_data = principle_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(principle, field, value)

    await db.commit()
    await db.refresh(principle)
    return principle


@router.delete("/principles/{principle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ekom_principle(
    principle_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role(UserRole.ADMIN))],
) -> None:
    """Slett et Ekomforskriften-prinsipp."""
    result = await db.execute(
        select(EkomPrinciple).where(EkomPrinciple.id == principle_id)
    )
    principle = result.scalar_one_or_none()

    if not principle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prinsipp ikke funnet",
        )

    await db.delete(principle)
    await db.commit()


# Risk Mappings

@router.get("/mappings", response_model=list[EkomMappingResponse])
async def list_ekom_mappings(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_active_user)],
    risk_id: int | None = None,
    principle_id: int | None = None,
    compliance_status: str | None = None,
) -> list[EkomMapping]:
    """List alle Ekomforskriften-koblinger for risikoer."""
    query = select(EkomMapping)

    if risk_id:
        query = query.where(EkomMapping.risk_id == risk_id)

    if principle_id:
        query = query.where(EkomMapping.ekom_principle_id == principle_id)

    if compliance_status:
        query = query.where(EkomMapping.compliance_status == compliance_status)

    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("/mappings", response_model=EkomMappingResponse, status_code=status.HTTP_201_CREATED)
async def create_ekom_mapping(
    mapping_data: EkomMappingCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[
        User,
        Depends(require_role(UserRole.ADMIN, UserRole.RISIKOANSVARLIG)),
    ],
) -> EkomMapping:
    """Opprett kobling mellom risiko og Ekomforskriften-prinsipp."""
    # Verify risk exists
    risk_result = await db.execute(
        select(Risk).where(Risk.id == mapping_data.risk_id)
    )
    if not risk_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Risiko ikke funnet",
        )

    # Verify principle exists
    principle_result = await db.execute(
        select(EkomPrinciple).where(EkomPrinciple.id == mapping_data.ekom_principle_id)
    )
    if not principle_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ekomforskriften-prinsipp ikke funnet",
        )

    # Check if mapping already exists
    existing = await db.execute(
        select(EkomMapping)
        .where(
            EkomMapping.risk_id == mapping_data.risk_id,
            EkomMapping.ekom_principle_id == mapping_data.ekom_principle_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Kobling finnes allerede",
        )

    mapping = EkomMapping(**mapping_data.model_dump())
    db.add(mapping)
    await db.commit()
    await db.refresh(mapping)
    return mapping


@router.patch("/mappings/{mapping_id}", response_model=EkomMappingResponse)
async def update_ekom_mapping(
    mapping_id: int,
    mapping_data: EkomMappingUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[
        User,
        Depends(require_role(UserRole.ADMIN, UserRole.RISIKOANSVARLIG)),
    ],
) -> EkomMapping:
    """Oppdater Ekomforskriften-kobling."""
    result = await db.execute(
        select(EkomMapping).where(EkomMapping.id == mapping_id)
    )
    mapping = result.scalar_one_or_none()

    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kobling ikke funnet",
        )

    update_data = mapping_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(mapping, field, value)

    await db.commit()
    await db.refresh(mapping)
    return mapping


@router.delete("/mappings/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ekom_mapping(
    mapping_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[
        User,
        Depends(require_role(UserRole.ADMIN, UserRole.RISIKOANSVARLIG)),
    ],
) -> None:
    """Slett Ekomforskriften-kobling."""
    result = await db.execute(
        select(EkomMapping).where(EkomMapping.id == mapping_id)
    )
    mapping = result.scalar_one_or_none()

    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kobling ikke funnet",
        )

    await db.delete(mapping)
    await db.commit()


# Action Mappings

@router.post("/action-mappings", response_model=EkomActionMappingResponse, status_code=status.HTTP_201_CREATED)
async def create_ekom_action_mapping(
    mapping_data: EkomActionMappingCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[
        User,
        Depends(require_role(UserRole.ADMIN, UserRole.RISIKOANSVARLIG)),
    ],
) -> EkomActionMapping:
    """Opprett kobling mellom tiltak og Ekomforskriften-prinsipp."""
    # Verify action exists
    action_result = await db.execute(
        select(Action).where(Action.id == mapping_data.action_id)
    )
    if not action_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tiltak ikke funnet",
        )

    # Verify principle exists
    principle_result = await db.execute(
        select(EkomPrinciple).where(EkomPrinciple.id == mapping_data.ekom_principle_id)
    )
    if not principle_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ekomforskriften-prinsipp ikke funnet",
        )

    # Check if mapping already exists
    existing = await db.execute(
        select(EkomActionMapping)
        .where(
            EkomActionMapping.action_id == mapping_data.action_id,
            EkomActionMapping.ekom_principle_id == mapping_data.ekom_principle_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Kobling finnes allerede",
        )

    mapping = EkomActionMapping(**mapping_data.model_dump())
    db.add(mapping)
    await db.commit()
    await db.refresh(mapping)
    return mapping


@router.delete("/action-mappings/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ekom_action_mapping(
    mapping_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[
        User,
        Depends(require_role(UserRole.ADMIN, UserRole.RISIKOANSVARLIG)),
    ],
) -> None:
    """Slett tiltak-Ekomforskriften-kobling."""
    result = await db.execute(
        select(EkomActionMapping).where(EkomActionMapping.id == mapping_id)
    )
    mapping = result.scalar_one_or_none()

    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kobling ikke funnet",
        )

    await db.delete(mapping)
    await db.commit()


# Compliance Reports

@router.get("/compliance/summary", response_model=EkomComplianceSummary)
async def get_ekom_compliance_summary(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_active_user)],
    project_id: int | None = None,
) -> EkomComplianceSummary:
    """Hent sammendrag av Ekomforskriften-samsvar."""
    # Total principles
    total_result = await db.execute(select(func.count(EkomPrinciple.id)))
    total_principles = total_result.scalar() or 0

    # Risks with mappings
    risks_query = select(func.count(distinct(EkomMapping.risk_id)))
    if project_id:
        risks_query = risks_query.join(Risk).where(Risk.project_id == project_id)
    risks_result = await db.execute(risks_query)
    risks_with_mapping = risks_result.scalar() or 0

    # Compliance status counts
    status_query = select(EkomMapping.compliance_status, func.count(EkomMapping.id)).group_by(
        EkomMapping.compliance_status
    )
    if project_id:
        status_query = status_query.join(Risk).where(Risk.project_id == project_id)
    status_result = await db.execute(status_query)
    status_counts = {row[0]: row[1] for row in status_result.all()}

    compliant = status_counts.get("compliant", 0)
    partial = status_counts.get("partial", 0)
    non_compliant = status_counts.get("non_compliant", 0)
    not_assessed = status_counts.get("not_assessed", 0) + status_counts.get(None, 0)

    total_assessed = compliant + partial + non_compliant + not_assessed
    coverage = (compliant + partial) / total_assessed * 100 if total_assessed > 0 else 0

    return EkomComplianceSummary(
        total_principles=total_principles,
        risks_with_mapping=risks_with_mapping,
        compliant=compliant,
        partial=partial,
        non_compliant=non_compliant,
        not_assessed=not_assessed,
        coverage_percentage=round(coverage, 1),
    )


@router.get("/compliance/by-category", response_model=list[EkomComplianceByCategory])
async def get_ekom_compliance_by_category(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_active_user)],
) -> list[EkomComplianceByCategory]:
    """Hent Ekomforskriften-samsvar per kategori."""
    results = []

    for category in EkomCategory:
        # Get principles in this category
        principles_result = await db.execute(
            select(EkomPrinciple.id).where(EkomPrinciple.category == category)
        )
        principle_ids = [row[0] for row in principles_result.all()]

        if not principle_ids:
            continue

        # Get mappings for these principles
        mappings_result = await db.execute(
            select(EkomMapping.compliance_status, func.count(EkomMapping.id))
            .where(EkomMapping.ekom_principle_id.in_(principle_ids))
            .group_by(EkomMapping.compliance_status)
        )
        status_counts = {row[0]: row[1] for row in mappings_result.all()}

        results.append(EkomComplianceByCategory(
            category=category.name,
            category_label=category.value,
            total=len(principle_ids),
            compliant=status_counts.get("compliant", 0),
            partial=status_counts.get("partial", 0),
            non_compliant=status_counts.get("non_compliant", 0),
            not_assessed=status_counts.get("not_assessed", 0) + status_counts.get(None, 0),
        ))

    return results


@router.get("/compliance/gaps")
async def get_ekom_compliance_gaps(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_active_user)],
) -> list[dict]:
    """Hent Ekomforskriften-prinsipper uten risikokobling (gap-analyse)."""
    # Get all principle IDs
    all_principles = await db.execute(
        select(EkomPrinciple).order_by(EkomPrinciple.sort_order)
    )
    principles = list(all_principles.scalars().all())

    # Get principle IDs with mappings
    mapped_result = await db.execute(
        select(distinct(EkomMapping.ekom_principle_id))
    )
    mapped_ids = {row[0] for row in mapped_result.all()}

    # Find unmapped principles
    gaps = []
    for principle in principles:
        if principle.id not in mapped_ids:
            gaps.append({
                "id": principle.id,
                "code": principle.code,
                "full_code": principle.full_code,
                "title": principle.title,
                "category": principle.category.value,
                "description": principle.description,
            })

    return gaps


@router.get("/risks/{risk_id}/mappings", response_model=list[EkomMappingResponse])
async def get_risk_ekom_mappings(
    risk_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_active_user)],
) -> list[EkomMapping]:
    """Hent alle Ekomforskriften-koblinger for en risiko."""
    # Verify risk exists
    risk_result = await db.execute(select(Risk).where(Risk.id == risk_id))
    if not risk_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Risiko ikke funnet",
        )

    result = await db.execute(
        select(EkomMapping)
        .where(EkomMapping.risk_id == risk_id)
        .options(selectinload(EkomMapping.ekom_principle))
    )
    return list(result.scalars().all())
