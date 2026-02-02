"""
Audit endpoints for NetROS.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user, require_role
from app.database import get_db
from app.models.audit import AuditAction
from app.models.user import User, UserRole
from app.services.audit_service import AuditService

router = APIRouter()


@router.get("/entity/{entity_type}/{entity_id}")
async def get_entity_audit_history(
    entity_type: str,
    entity_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role(UserRole.ADMIN, UserRole.RISIKOANSVARLIG))],
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[dict]:
    """
    Hent audit-historikk for en spesifikk entitet.

    Tilgjengelig for admin og risikoansvarlig.
    """
    audit_service = AuditService(db)
    logs = await audit_service.get_entity_history(
        entity_type=entity_type,
        entity_id=entity_id,
        limit=limit,
        offset=offset,
    )

    return [
        {
            "id": log.id,
            "timestamp": log.timestamp.isoformat(),
            "action": log.action.value,
            "user_id": log.user_id,
            "username": log.user.username if log.user else None,
            "description": log.description,
            "old_values": log.old_values,
            "new_values": log.new_values,
        }
        for log in logs
    ]


@router.get("/user/{user_id}")
async def get_user_audit_history(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[dict]:
    """
    Hent audit-historikk for en spesifikk bruker.

    Kun tilgjengelig for admin.
    """
    audit_service = AuditService(db)
    logs = await audit_service.get_user_activity(
        user_id=user_id,
        limit=limit,
        offset=offset,
    )

    return [
        {
            "id": log.id,
            "timestamp": log.timestamp.isoformat(),
            "action": log.action.value,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "description": log.description,
        }
        for log in logs
    ]


@router.get("/recent")
async def get_recent_audit_activity(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role(UserRole.ADMIN, UserRole.RISIKOANSVARLIG))],
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    action: str | None = Query(None, description="Filter by action type"),
    entity_type: str | None = Query(None, description="Filter by entity type"),
) -> list[dict]:
    """
    Hent nylig audit-aktivitet.

    Tilgjengelig for admin og risikoansvarlig.
    """
    action_filter = None
    if action:
        try:
            action_filter = AuditAction(action)
        except ValueError:
            pass

    audit_service = AuditService(db)
    logs = await audit_service.get_recent_activity(
        limit=limit,
        offset=offset,
        action_filter=action_filter,
        entity_type_filter=entity_type,
    )

    return [
        {
            "id": log.id,
            "timestamp": log.timestamp.isoformat(),
            "action": log.action.value,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "user_id": log.user_id,
            "username": log.user.username if log.user else None,
            "description": log.description,
        }
        for log in logs
    ]


@router.get("/my-activity")
async def get_my_audit_activity(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[dict]:
    """
    Hent min egen audit-historikk.

    Tilgjengelig for alle innloggede brukere.
    """
    audit_service = AuditService(db)
    logs = await audit_service.get_user_activity(
        user_id=current_user.id,
        limit=limit,
        offset=offset,
    )

    return [
        {
            "id": log.id,
            "timestamp": log.timestamp.isoformat(),
            "action": log.action.value,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "description": log.description,
        }
        for log in logs
    ]
