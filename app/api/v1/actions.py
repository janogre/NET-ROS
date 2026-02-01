"""
Action endpoints for NetROS.
"""

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_active_user, require_role
from app.database import get_db
from app.models.action import Action, ActionStatus, RiskAction
from app.models.user import User, UserRole
from app.schemas.action import ActionCreate, ActionUpdate, ActionResponse

router = APIRouter()


@router.get("/", response_model=list[ActionResponse])
async def list_actions(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_active_user)],
    skip: int = 0,
    limit: int = 100,
    status_filter: str | None = None,
) -> list[Action]:
    """List alle tiltak."""
    query = select(Action).options(selectinload(Action.assignee))

    if status_filter:
        query = query.where(Action.status == status_filter)

    query = query.order_by(Action.due_date.asc().nullslast()).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/overdue", response_model=list[ActionResponse])
async def list_overdue_actions(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_active_user)],
) -> list[Action]:
    """List forfalte tiltak."""
    from datetime import date

    result = await db.execute(
        select(Action)
        .options(selectinload(Action.assignee))
        .where(
            Action.status.not_in([ActionStatus.FULLFORT, ActionStatus.AVBRUTT]),
            Action.due_date < date.today(),
        )
        .order_by(Action.due_date.asc())
    )
    return list(result.scalars().all())


@router.post("/", response_model=ActionResponse, status_code=status.HTTP_201_CREATED)
async def create_action(
    action_data: ActionCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(
            require_role(UserRole.ADMIN, UserRole.RISIKOANSVARLIG, UserRole.BRUKER)
        ),
    ],
) -> Action:
    """Opprett nytt tiltak."""
    action = Action(
        title=action_data.title,
        description=action_data.description,
        priority=action_data.priority,
        status=action_data.status,
        due_date=action_data.due_date,
        assignee_id=action_data.assignee_id or current_user.id,
        responsible_department_id=action_data.responsible_department_id,
    )
    db.add(action)
    await db.flush()

    # Add risk associations
    for risk_id in action_data.risk_ids:
        risk_action = RiskAction(risk_id=risk_id, action_id=action.id)
        db.add(risk_action)

    await db.commit()
    await db.refresh(action)
    return action


@router.get("/{action_id}", response_model=ActionResponse)
async def get_action(
    action_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_active_user)],
) -> Action:
    """Hent et tiltak."""
    result = await db.execute(
        select(Action)
        .options(selectinload(Action.assignee))
        .where(Action.id == action_id)
    )
    action = result.scalar_one_or_none()

    if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tiltak ikke funnet",
        )

    return action


@router.patch("/{action_id}", response_model=ActionResponse)
async def update_action(
    action_id: int,
    action_data: ActionUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[
        User,
        Depends(
            require_role(UserRole.ADMIN, UserRole.RISIKOANSVARLIG, UserRole.BRUKER)
        ),
    ],
) -> Action:
    """Oppdater et tiltak."""
    result = await db.execute(select(Action).where(Action.id == action_id))
    action = result.scalar_one_or_none()

    if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tiltak ikke funnet",
        )

    update_data = action_data.model_dump(exclude_unset=True)
    risk_ids = update_data.pop("risk_ids", None)

    # Handle status change to completed
    if update_data.get("status") == ActionStatus.FULLFORT and not action.completed_at:
        update_data["completed_at"] = datetime.now(timezone.utc)

    for field, value in update_data.items():
        setattr(action, field, value)

    # Update risk associations if provided
    if risk_ids is not None:
        await db.execute(
            RiskAction.__table__.delete().where(RiskAction.action_id == action_id)
        )
        for risk_id in risk_ids:
            risk_action = RiskAction(risk_id=risk_id, action_id=action.id)
            db.add(risk_action)

    await db.commit()
    await db.refresh(action)
    return action


@router.patch("/{action_id}/status", response_model=ActionResponse)
async def update_action_status(
    action_id: int,
    new_status: ActionStatus,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[
        User,
        Depends(
            require_role(UserRole.ADMIN, UserRole.RISIKOANSVARLIG, UserRole.BRUKER)
        ),
    ],
) -> Action:
    """Oppdater status på et tiltak."""
    result = await db.execute(select(Action).where(Action.id == action_id))
    action = result.scalar_one_or_none()

    if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tiltak ikke funnet",
        )

    action.status = new_status
    if new_status == ActionStatus.FULLFORT:
        action.completed_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(action)
    return action


@router.delete("/{action_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_action(
    action_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role(UserRole.ADMIN, UserRole.RISIKOANSVARLIG))],
) -> None:
    """Slett et tiltak."""
    result = await db.execute(select(Action).where(Action.id == action_id))
    action = result.scalar_one_or_none()

    if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tiltak ikke funnet",
        )

    await db.delete(action)
    await db.commit()
