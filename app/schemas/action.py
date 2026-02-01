"""
Pydantic schemas for Action.
"""

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.action import ActionPriority, ActionStatus


class ActionBase(BaseModel):
    """Base schema for Action."""

    title: str = Field(..., min_length=1, max_length=300)
    description: str | None = None
    priority: ActionPriority = ActionPriority.MIDDELS
    status: ActionStatus = ActionStatus.PLANLAGT
    due_date: date | None = None
    assignee_id: int | None = None
    responsible_department_id: int | None = None


class ActionCreate(ActionBase):
    """Schema for creating an action."""

    risk_ids: list[int] = []


class ActionUpdate(BaseModel):
    """Schema for updating an action."""

    title: str | None = Field(None, min_length=1, max_length=300)
    description: str | None = None
    priority: ActionPriority | None = None
    status: ActionStatus | None = None
    due_date: date | None = None
    assignee_id: int | None = None
    responsible_department_id: int | None = None
    risk_ids: list[int] | None = None


class ActionResponse(ActionBase):
    """Schema for action response."""

    id: int
    completed_at: datetime | None = None
    is_overdue: bool = False
    priority_label: str = ""
    status_label: str = ""
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
