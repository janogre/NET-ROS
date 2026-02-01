"""
Pydantic schemas for Review.
"""

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.review import ReviewType


class ReviewBase(BaseModel):
    """Base schema for Review."""

    title: str = Field(..., min_length=1, max_length=300)
    review_type: ReviewType = ReviewType.PERIODISK
    scheduled_date: date | None = None
    conductor_id: int | None = None
    incident_reference: str | None = None
    incident_date: date | None = None


class ReviewCreate(ReviewBase):
    """Schema for creating a review."""

    risk_ids: list[int] = []


class ReviewUpdate(BaseModel):
    """Schema for updating a review."""

    title: str | None = Field(None, min_length=1, max_length=300)
    review_type: ReviewType | None = None
    scheduled_date: date | None = None
    conducted_date: date | None = None
    next_review_date: date | None = None
    conductor_id: int | None = None
    findings: str | None = None
    conclusions: str | None = None
    incident_reference: str | None = None
    incident_date: date | None = None
    risk_ids: list[int] | None = None


class ReviewResponse(ReviewBase):
    """Schema for review response."""

    id: int
    conducted_date: date | None = None
    next_review_date: date | None = None
    findings: str | None = None
    conclusions: str | None = None
    is_completed: bool = False
    review_type_label: str = ""
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
