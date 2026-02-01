"""
Pydantic schemas for InformationAsset.
"""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.information_asset import Classification, DataType


class InformationAssetBase(BaseModel):
    """Base schema for InformationAsset."""

    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    classification: Classification = Classification.INTERN
    data_types: list[str] = []
    owner_department_id: int | None = None


class InformationAssetCreate(InformationAssetBase):
    """Schema for creating an information asset."""

    pass


class InformationAssetUpdate(BaseModel):
    """Schema for updating an information asset."""

    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    classification: Classification | None = None
    data_types: list[str] | None = None
    owner_department_id: int | None = None


class InformationAssetResponse(InformationAssetBase):
    """Schema for information asset response."""

    id: int
    classification_label: str = ""
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InformationAssetListResponse(BaseModel):
    """Schema for listing information assets."""

    items: list[InformationAssetResponse]
    total: int
