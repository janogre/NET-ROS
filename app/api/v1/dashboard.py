"""
Dashboard endpoints for NetROS.
"""

from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user
from app.database import get_db
from app.models.asset import Asset
from app.models.risk import Risk, NSMMapping
from app.models.action import Action, ActionStatus
from app.models.review import Review
from app.models.supplier import Supplier
from app.models.user import User
from app.schemas.dashboard import DashboardSummary, RiskDistribution, ActionProgress
from app.services.risk_service import RiskService

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_active_user)],
) -> DashboardSummary:
    """Hent sammendrag for dashboard."""
    # Count assets
    asset_count = await db.execute(select(func.count(Asset.id)))
    total_assets = asset_count.scalar() or 0

    # Count risks
    risk_count = await db.execute(select(func.count(Risk.id)))
    total_risks = risk_count.scalar() or 0

    # Count actions
    action_count = await db.execute(select(func.count(Action.id)))
    total_actions = action_count.scalar() or 0

    # Count overdue actions
    overdue_count = await db.execute(
        select(func.count(Action.id)).where(
            Action.status.not_in([ActionStatus.FULLFORT, ActionStatus.AVBRUTT]),
            Action.due_date < date.today(),
        )
    )
    overdue_actions = overdue_count.scalar() or 0

    # Count upcoming reviews (next 30 days)
    upcoming_date = date.today() + timedelta(days=30)
    upcoming_count = await db.execute(
        select(func.count(Review.id)).where(
            Review.conducted_date.is_(None),
            Review.scheduled_date <= upcoming_date,
        )
    )
    upcoming_reviews = upcoming_count.scalar() or 0

    # Get risk distribution
    risk_service = RiskService(db)
    dist = await risk_service.get_risk_distribution()
    risk_distribution = RiskDistribution(
        green=dist["green"],
        yellow=dist["yellow"],
        orange=dist["orange"],
        red=dist["red"],
        total=sum(dist.values()),
    )

    # Get action progress
    action_stats = await db.execute(
        select(Action.status, func.count(Action.id)).group_by(Action.status)
    )
    action_counts = {row[0]: row[1] for row in action_stats.all()}

    action_progress = ActionProgress(
        planlagt=action_counts.get(ActionStatus.PLANLAGT, 0),
        pagaende=action_counts.get(ActionStatus.PAGAENDE, 0),
        fullfort=action_counts.get(ActionStatus.FULLFORT, 0),
        forfalt=overdue_actions,
        total=total_actions,
    )

    # Get recent risks (last 5)
    recent_result = await db.execute(
        select(Risk).order_by(Risk.created_at.desc()).limit(5)
    )
    recent_risks = [
        {
            "id": r.id,
            "title": r.title,
            "risk_score": r.risk_score,
            "risk_level": r.risk_level,
            "created_at": r.created_at.isoformat(),
        }
        for r in recent_result.scalars().all()
    ]

    # Get critical risks (score >= 17)
    critical_result = await db.execute(
        select(Risk)
        .where(Risk.likelihood * Risk.consequence >= 17)
        .order_by((Risk.likelihood * Risk.consequence).desc())
        .limit(5)
    )
    critical_risks = [
        {
            "id": r.id,
            "title": r.title,
            "risk_score": r.risk_score,
            "risk_level": r.risk_level,
            "status": r.status.value,
        }
        for r in critical_result.scalars().all()
    ]

    return DashboardSummary(
        total_assets=total_assets,
        total_risks=total_risks,
        total_actions=total_actions,
        overdue_actions=overdue_actions,
        upcoming_reviews=upcoming_reviews,
        risk_distribution=risk_distribution,
        action_progress=action_progress,
        recent_risks=recent_risks,
        critical_risks=critical_risks,
    )


@router.get("/risk-distribution")
async def get_risk_distribution(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_active_user)],
    project_id: int | None = None,
) -> dict:
    """Hent risikofordeling."""
    risk_service = RiskService(db)
    return await risk_service.get_risk_distribution(project_id)


@router.get("/action-progress")
async def get_action_progress(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """Hent tiltaksfremdrift."""
    action_stats = await db.execute(
        select(Action.status, func.count(Action.id)).group_by(Action.status)
    )
    counts = {row[0].value: row[1] for row in action_stats.all()}

    # Count overdue
    overdue_count = await db.execute(
        select(func.count(Action.id)).where(
            Action.status.not_in([ActionStatus.FULLFORT, ActionStatus.AVBRUTT]),
            Action.due_date < date.today(),
        )
    )
    counts["forfalt"] = overdue_count.scalar() or 0

    return counts


@router.get("/alerts")
async def get_alerts(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_active_user)],
    include_info: bool = Query(True, description="Inkluder info-varsler"),
    include_warning: bool = Query(True, description="Inkluder advarsels-varsler"),
    include_danger: bool = Query(True, description="Inkluder kritiske varsler"),
) -> list[dict]:
    """
    Hent varsler for dashboard.

    Varsler inkluderer:
    - Forfalte tiltak (warning)
    - Høye risikoer som krever handling (danger)
    - Kommende gjennomganger (info)
    - Kontraktsutløp for leverandører (warning/danger)
    - Risikoer uten NSM-mapping (info)
    - Kritiske leverandører uten vurdering (warning)
    - Forfalte gjennomganger (warning)
    """
    alerts = []

    # Overdue actions (warning)
    if include_warning:
        overdue_result = await db.execute(
            select(Action).where(
                Action.status.not_in([ActionStatus.FULLFORT, ActionStatus.AVBRUTT]),
                Action.due_date < date.today(),
            )
        )
        overdue_actions = overdue_result.scalars().all()
        for action in overdue_actions:
            days_overdue = (date.today() - action.due_date).days if action.due_date else 0
            alerts.append({
                "type": "warning",
                "category": "tiltak",
                "message": f"Tiltak forfalt ({days_overdue} dager): {action.title}",
                "entity_id": action.id,
                "entity_type": "action",
                "due_date": action.due_date.isoformat() if action.due_date else None,
                "days_overdue": days_overdue,
            })

    # High-risk items (danger)
    if include_danger:
        high_risk_result = await db.execute(
            select(Risk).where(
                Risk.likelihood * Risk.consequence >= 17,
                Risk.status.not_in(["lukket", "akseptert"]),
            )
        )
        high_risks = high_risk_result.scalars().all()
        for risk in high_risks:
            alerts.append({
                "type": "danger",
                "category": "risiko",
                "message": f"Høy risiko krever handling: {risk.title}",
                "entity_id": risk.id,
                "entity_type": "risk",
                "risk_score": risk.risk_score,
            })

    # Upcoming reviews (info)
    if include_info:
        upcoming_date = date.today() + timedelta(days=7)
        upcoming_result = await db.execute(
            select(Review).where(
                Review.conducted_date.is_(None),
                Review.scheduled_date <= upcoming_date,
                Review.scheduled_date >= date.today(),
            )
        )
        upcoming_reviews = upcoming_result.scalars().all()
        for review in upcoming_reviews:
            days_until = (review.scheduled_date - date.today()).days if review.scheduled_date else 0
            alerts.append({
                "type": "info",
                "category": "gjennomgang",
                "message": f"Planlagt gjennomgang om {days_until} dag(er): {review.title}",
                "entity_id": review.id,
                "entity_type": "review",
                "scheduled_date": review.scheduled_date.isoformat() if review.scheduled_date else None,
                "days_until": days_until,
            })

    # Overdue reviews (warning)
    if include_warning:
        overdue_review_result = await db.execute(
            select(Review).where(
                Review.conducted_date.is_(None),
                Review.scheduled_date < date.today(),
            )
        )
        overdue_reviews = overdue_review_result.scalars().all()
        for review in overdue_reviews:
            days_overdue = (date.today() - review.scheduled_date).days if review.scheduled_date else 0
            alerts.append({
                "type": "warning",
                "category": "gjennomgang",
                "message": f"Gjennomgang forfalt ({days_overdue} dager): {review.title}",
                "entity_id": review.id,
                "entity_type": "review",
                "scheduled_date": review.scheduled_date.isoformat() if review.scheduled_date else None,
                "days_overdue": days_overdue,
            })

    # Contract expiry alerts (30/60/90 days)
    for days, alert_type in [(30, "danger"), (60, "warning"), (90, "info")]:
        if (alert_type == "danger" and not include_danger) or \
           (alert_type == "warning" and not include_warning) or \
           (alert_type == "info" and not include_info):
            continue

        expiry_date = date.today() + timedelta(days=days)
        prev_date = date.today() + timedelta(days=days - 30) if days > 30 else date.today()

        contract_result = await db.execute(
            select(Supplier).where(
                Supplier.contract_expiry.isnot(None),
                Supplier.contract_expiry <= expiry_date,
                Supplier.contract_expiry > prev_date,
            )
        )
        expiring_suppliers = contract_result.scalars().all()
        for supplier in expiring_suppliers:
            days_until = (supplier.contract_expiry - date.today()).days if supplier.contract_expiry else 0
            alerts.append({
                "type": alert_type,
                "category": "kontrakt",
                "message": f"Kontrakt utløper om {days_until} dag(er): {supplier.name}",
                "entity_id": supplier.id,
                "entity_type": "supplier",
                "contract_expiry": supplier.contract_expiry.isoformat() if supplier.contract_expiry else None,
                "days_until_expiry": days_until,
                "criticality": supplier.criticality,
            })

    # Risks without NSM mapping (info)
    if include_info:
        # Get risk IDs that have NSM mappings
        mapped_risks_result = await db.execute(
            select(distinct(NSMMapping.risk_id))
        )
        mapped_risk_ids = {row[0] for row in mapped_risks_result.all()}

        # Get active risks without mapping
        unmapped_result = await db.execute(
            select(Risk).where(
                Risk.status.not_in(["lukket", "akseptert"]),
                Risk.id.not_in(mapped_risk_ids) if mapped_risk_ids else True,
            ).limit(10)
        )
        unmapped_risks = unmapped_result.scalars().all()
        for risk in unmapped_risks:
            alerts.append({
                "type": "info",
                "category": "nsm_dekning",
                "message": f"Risiko mangler NSM-mapping: {risk.title}",
                "entity_id": risk.id,
                "entity_type": "risk",
                "risk_score": risk.risk_score,
            })

    # Critical suppliers without recent assessment (warning)
    if include_warning:
        critical_suppliers_result = await db.execute(
            select(Supplier).where(
                Supplier.criticality >= 4,
            )
        )
        critical_suppliers = critical_suppliers_result.scalars().all()
        for supplier in critical_suppliers:
            alerts.append({
                "type": "warning",
                "category": "leverandør",
                "message": f"Kritisk leverandør - vurder risiko: {supplier.name}",
                "entity_id": supplier.id,
                "entity_type": "supplier",
                "criticality": supplier.criticality,
                "criticality_label": supplier.criticality_label,
            })

    # Sort alerts by type priority (danger > warning > info)
    type_priority = {"danger": 0, "warning": 1, "info": 2}
    alerts.sort(key=lambda x: type_priority.get(x["type"], 3))

    return alerts


@router.get("/alerts/count")
async def get_alerts_count(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """Hent antall varsler per type."""
    # Overdue actions
    overdue_actions_count = await db.execute(
        select(func.count(Action.id)).where(
            Action.status.not_in([ActionStatus.FULLFORT, ActionStatus.AVBRUTT]),
            Action.due_date < date.today(),
        )
    )
    overdue_actions = overdue_actions_count.scalar() or 0

    # High risks
    high_risks_count = await db.execute(
        select(func.count(Risk.id)).where(
            Risk.likelihood * Risk.consequence >= 17,
            Risk.status.not_in(["lukket", "akseptert"]),
        )
    )
    high_risks = high_risks_count.scalar() or 0

    # Overdue reviews
    overdue_reviews_count = await db.execute(
        select(func.count(Review.id)).where(
            Review.conducted_date.is_(None),
            Review.scheduled_date < date.today(),
        )
    )
    overdue_reviews = overdue_reviews_count.scalar() or 0

    # Expiring contracts (30 days)
    expiring_contracts_count = await db.execute(
        select(func.count(Supplier.id)).where(
            Supplier.contract_expiry.isnot(None),
            Supplier.contract_expiry <= date.today() + timedelta(days=30),
            Supplier.contract_expiry >= date.today(),
        )
    )
    expiring_contracts = expiring_contracts_count.scalar() or 0

    return {
        "total": overdue_actions + high_risks + overdue_reviews + expiring_contracts,
        "danger": high_risks + expiring_contracts,
        "warning": overdue_actions + overdue_reviews,
        "by_category": {
            "tiltak_forfalt": overdue_actions,
            "hoye_risikoer": high_risks,
            "gjennomganger_forfalt": overdue_reviews,
            "kontrakter_utloper": expiring_contracts,
        },
    }
