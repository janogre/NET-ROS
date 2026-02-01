"""
Pydantic schemas for Project.
"""

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.project import ProjectType, ProjectStatus


class ProjectBase(BaseModel):
    """Base schema for Project."""

    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    project_type: ProjectType = ProjectType.PERIODISK_ROS
    status: ProjectStatus = ProjectStatus.PLANLAGT
    scheduled_date: date | None = None
    owner_id: int | None = None
    owner_department_id: int | None = None


class ProjectCreate(ProjectBase):
    """Schema for creating a project."""

    pass


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""

    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    project_type: ProjectType | None = None
    status: ProjectStatus | None = None
    scheduled_date: date | None = None
    completed_date: date | None = None
    owner_id: int | None = None
    owner_department_id: int | None = None


class ProjectResponse(ProjectBase):
    """Schema for project response."""

    id: int
    completed_date: date | None = None
    created_at: datetime
    updated_at: datetime
    risk_count: int = 0

    model_config = {"from_attributes": True}
