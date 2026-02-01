"""
Project endpoints for NetROS.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user, require_role
from app.database import get_db
from app.models.project import Project
from app.models.risk import Risk
from app.models.user import User, UserRole
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse

router = APIRouter()


@router.get("/", response_model=list[ProjectResponse])
async def list_projects(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_active_user)],
    skip: int = 0,
    limit: int = 100,
) -> list[dict]:
    """List alle prosjekter."""
    result = await db.execute(
        select(Project).order_by(Project.created_at.desc()).offset(skip).limit(limit)
    )
    projects = result.scalars().all()

    # Get risk counts
    response = []
    for project in projects:
        count_result = await db.execute(
            select(func.count(Risk.id)).where(Risk.project_id == project.id)
        )
        risk_count = count_result.scalar() or 0
        project_dict = {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "project_type": project.project_type,
            "status": project.status,
            "scheduled_date": project.scheduled_date,
            "completed_date": project.completed_date,
            "owner_id": project.owner_id,
            "owner_department_id": project.owner_department_id,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
            "risk_count": risk_count,
        }
        response.append(project_dict)

    return response


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[
        User, Depends(require_role(UserRole.ADMIN, UserRole.RISIKOANSVARLIG))
    ],
) -> dict:
    """Opprett nytt prosjekt."""
    project = Project(
        name=project_data.name,
        description=project_data.description,
        project_type=project_data.project_type,
        status=project_data.status,
        scheduled_date=project_data.scheduled_date,
        owner_id=project_data.owner_id or current_user.id,
        owner_department_id=project_data.owner_department_id,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)

    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "project_type": project.project_type,
        "status": project.status,
        "scheduled_date": project.scheduled_date,
        "completed_date": project.completed_date,
        "owner_id": project.owner_id,
        "owner_department_id": project.owner_department_id,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
        "risk_count": 0,
    }


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """Hent et prosjekt."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prosjekt ikke funnet",
        )

    count_result = await db.execute(
        select(func.count(Risk.id)).where(Risk.project_id == project.id)
    )
    risk_count = count_result.scalar() or 0

    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "project_type": project.project_type,
        "status": project.status,
        "scheduled_date": project.scheduled_date,
        "completed_date": project.completed_date,
        "owner_id": project.owner_id,
        "owner_department_id": project.owner_department_id,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
        "risk_count": risk_count,
    }


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[
        User, Depends(require_role(UserRole.ADMIN, UserRole.RISIKOANSVARLIG))
    ],
) -> dict:
    """Oppdater et prosjekt."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prosjekt ikke funnet",
        )

    update_data = project_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    await db.commit()
    await db.refresh(project)

    count_result = await db.execute(
        select(func.count(Risk.id)).where(Risk.project_id == project.id)
    )
    risk_count = count_result.scalar() or 0

    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "project_type": project.project_type,
        "status": project.status,
        "scheduled_date": project.scheduled_date,
        "completed_date": project.completed_date,
        "owner_id": project.owner_id,
        "owner_department_id": project.owner_department_id,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
        "risk_count": risk_count,
    }


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role(UserRole.ADMIN))],
) -> None:
    """Slett et prosjekt (kun admin)."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prosjekt ikke funnet",
        )

    await db.delete(project)
    await db.commit()
