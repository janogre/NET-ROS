"""
Pydantic schemas for Department.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class DepartmentBase(BaseModel):
    """Base schema for Department."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    parent_id: int | None = None
    manager_id: int | None = None


class DepartmentCreate(DepartmentBase):
    """Schema for creating a department."""

    pass


class DepartmentUpdate(BaseModel):
    """Schema for updating a department."""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None
    parent_id: int | None = None
    manager_id: int | None = None


class DepartmentResponse(DepartmentBase):
    """Schema for department response."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
