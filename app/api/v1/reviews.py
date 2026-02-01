"""
Review endpoints for NetROS.
"""

from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_active_user, require_role
from app.database import get_db
from app.models.review import Review, ReviewRisk, ReviewType
from app.models.risk import Risk
from app.models.user import User, UserRole
from app.schemas.review import ReviewCreate, ReviewUpdate, ReviewResponse

router = APIRouter()


class ReviewStatus:
    """Hjelpeklasse for gjennomgangsstatus."""

    PLANLAGT = "planlagt"
    FORFALT = "forfalt"
    PAGAENDE = "pågående"
    FULLFORT = "fullført"


def get_review_status(review: Review) -> str:
    """Beregn status for en gjennomgang."""
    if review.conducted_date:
        return ReviewStatus.FULLFORT
    if review.scheduled_date:
        if review.scheduled_date < date.today():
            return ReviewStatus.FORFALT
        return ReviewStatus.PLANLAGT
    return ReviewStatus.PLANLAGT


@router.get("/", response_model=list[ReviewResponse])
async def list_reviews(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_active_user)],
    skip: int = 0,
    limit: int = 100,
    review_type: ReviewType | None = None,
    conductor_id: int | None = None,
    completed: bool | None = None,
    upcoming_days: int | None = Query(None, ge=0, description="Filtrer gjennomganger planlagt innen X dager"),
) -> list[Review]:
    """List alle gjennomganger."""
    query = select(Review)

    if review_type:
        query = query.where(Review.review_type == review_type)

    if conductor_id:
        query = query.where(Review.conductor_id == conductor_id)

    if completed is not None:
        if completed:
            query = query.where(Review.conducted_date.isnot(None))
        else:
            query = query.where(Review.conducted_date.is_(None))

    if upcoming_days is not None:
        future_date = date.today() + timedelta(days=upcoming_days)
        query = query.where(
            Review.conducted_date.is_(None),
            Review.scheduled_date.isnot(None),
            Review.scheduled_date <= future_date,
            Review.scheduled_date >= date.today(),
        )

    query = query.order_by(Review.scheduled_date.desc().nullslast()).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("/", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    review_data: ReviewCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_role(UserRole.ADMIN, UserRole.RISIKOANSVARLIG)),
    ],
) -> Review:
    """Opprett ny gjennomgang."""
    review = Review(
        title=review_data.title,
        review_type=review_data.review_type,
        scheduled_date=review_data.scheduled_date,
        conductor_id=review_data.conductor_id or current_user.id,
        incident_reference=review_data.incident_reference,
        incident_date=review_data.incident_date,
    )
    db.add(review)
    await db.flush()

    # Link risks if provided
    if review_data.risk_ids:
        for risk_id in review_data.risk_ids:
            # Verify risk exists
            risk_result = await db.execute(select(Risk).where(Risk.id == risk_id))
            if risk_result.scalar_one_or_none():
                link = ReviewRisk(review_id=review.id, risk_id=risk_id)
                db.add(link)

    await db.commit()
    await db.refresh(review)
    return review


@router.get("/overdue", response_model=list[ReviewResponse])
async def list_overdue_reviews(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_active_user)],
) -> list[Review]:
    """List forfalte gjennomganger."""
    query = (
        select(Review)
        .where(
            Review.conducted_date.is_(None),
            Review.scheduled_date.isnot(None),
            Review.scheduled_date < date.today(),
        )
        .order_by(Review.scheduled_date)
    )
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/statistics")
async def get_review_statistics(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """Hent statistikk for gjennomganger."""
    # Total count
    total_result = await db.execute(select(func.count(Review.id)))
    total = total_result.scalar() or 0

    # Completed
    completed_result = await db.execute(
        select(func.count(Review.id))
        .where(Review.conducted_date.isnot(None))
    )
    completed = completed_result.scalar() or 0

    # Overdue
    overdue_result = await db.execute(
        select(func.count(Review.id))
        .where(
            Review.conducted_date.is_(None),
            Review.scheduled_date.isnot(None),
            Review.scheduled_date < date.today(),
        )
    )
    overdue = overdue_result.scalar() or 0

    # Upcoming (next 30 days)
    upcoming_date = date.today() + timedelta(days=30)
    upcoming_result = await db.execute(
        select(func.count(Review.id))
        .where(
            Review.conducted_date.is_(None),
            Review.scheduled_date.isnot(None),
            Review.scheduled_date <= upcoming_date,
            Review.scheduled_date >= date.today(),
        )
    )
    upcoming = upcoming_result.scalar() or 0

    # By type
    type_result = await db.execute(
        select(Review.review_type, func.count(Review.id))
        .group_by(Review.review_type)
    )
    by_type = {row[0].value: row[1] for row in type_result.all()}

    return {
        "total": total,
        "completed": completed,
        "pending": total - completed,
        "overdue": overdue,
        "upcoming_30_days": upcoming,
        "by_type": by_type,
    }


@router.get("/{review_id}", response_model=ReviewResponse)
async def get_review(
    review_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_active_user)],
) -> Review:
    """Hent en gjennomgang."""
    result = await db.execute(
        select(Review).where(Review.id == review_id)
    )
    review = result.scalar_one_or_none()

    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gjennomgang ikke funnet",
        )

    return review


@router.patch("/{review_id}", response_model=ReviewResponse)
async def update_review(
    review_id: int,
    review_data: ReviewUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[
        User,
        Depends(require_role(UserRole.ADMIN, UserRole.RISIKOANSVARLIG)),
    ],
) -> Review:
    """Oppdater en gjennomgang."""
    result = await db.execute(
        select(Review).where(Review.id == review_id)
    )
    review = result.scalar_one_or_none()

    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gjennomgang ikke funnet",
        )

    update_data = review_data.model_dump(exclude_unset=True)

    # Handle risk_ids separately
    if "risk_ids" in update_data:
        risk_ids = update_data.pop("risk_ids")
        if risk_ids is not None:
            # Remove existing links
            existing_links = await db.execute(
                select(ReviewRisk).where(ReviewRisk.review_id == review_id)
            )
            for link in existing_links.scalars().all():
                await db.delete(link)

            # Add new links
            for risk_id in risk_ids:
                risk_result = await db.execute(select(Risk).where(Risk.id == risk_id))
                if risk_result.scalar_one_or_none():
                    link = ReviewRisk(review_id=review.id, risk_id=risk_id)
                    db.add(link)

    for field, value in update_data.items():
        setattr(review, field, value)

    await db.commit()
    await db.refresh(review)
    return review


@router.post("/{review_id}/complete", response_model=ReviewResponse)
async def complete_review(
    review_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[
        User,
        Depends(require_role(UserRole.ADMIN, UserRole.RISIKOANSVARLIG)),
    ],
    findings: str | None = None,
    conclusions: str | None = None,
    next_review_date: date | None = None,
) -> Review:
    """Marker gjennomgang som fullført."""
    result = await db.execute(
        select(Review).where(Review.id == review_id)
    )
    review = result.scalar_one_or_none()

    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gjennomgang ikke funnet",
        )

    review.conducted_date = date.today()
    if findings:
        review.findings = findings
    if conclusions:
        review.conclusions = conclusions
    if next_review_date:
        review.next_review_date = next_review_date

    await db.commit()
    await db.refresh(review)
    return review


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role(UserRole.ADMIN))],
) -> None:
    """Slett en gjennomgang."""
    result = await db.execute(
        select(Review).where(Review.id == review_id)
    )
    review = result.scalar_one_or_none()

    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gjennomgang ikke funnet",
        )

    await db.delete(review)
    await db.commit()


@router.get("/{review_id}/risks")
async def get_review_risks(
    review_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_active_user)],
) -> list[dict]:
    """Hent risikoer knyttet til en gjennomgang."""
    result = await db.execute(
        select(Review).where(Review.id == review_id)
    )
    review = result.scalar_one_or_none()

    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gjennomgang ikke funnet",
        )

    risks_result = await db.execute(
        select(Risk)
        .join(ReviewRisk)
        .where(ReviewRisk.review_id == review_id)
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


@router.post("/{review_id}/risks/{risk_id}", status_code=status.HTTP_201_CREATED)
async def link_review_to_risk(
    review_id: int,
    risk_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[
        User,
        Depends(require_role(UserRole.ADMIN, UserRole.RISIKOANSVARLIG)),
    ],
    notes: str | None = None,
) -> dict:
    """Koble gjennomgang til risiko."""
    # Verify review exists
    result = await db.execute(select(Review).where(Review.id == review_id))
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gjennomgang ikke funnet",
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
        select(ReviewRisk)
        .where(
            ReviewRisk.review_id == review_id,
            ReviewRisk.risk_id == risk_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Kobling finnes allerede",
        )

    link = ReviewRisk(
        review_id=review_id,
        risk_id=risk_id,
        notes=notes,
    )
    db.add(link)
    await db.commit()

    return {"message": "Kobling opprettet", "review_id": review_id, "risk_id": risk_id}


@router.delete("/{review_id}/risks/{risk_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unlink_review_from_risk(
    review_id: int,
    risk_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[
        User,
        Depends(require_role(UserRole.ADMIN, UserRole.RISIKOANSVARLIG)),
    ],
) -> None:
    """Fjern kobling mellom gjennomgang og risiko."""
    result = await db.execute(
        select(ReviewRisk)
        .where(
            ReviewRisk.review_id == review_id,
            ReviewRisk.risk_id == risk_id,
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
