"""
Pydantic schemas for Asset.
"""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.asset import AssetType, AssetCategory


class AssetBase(BaseModel):
    """Base schema for Asset."""

    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    asset_type: AssetType = AssetType.FYSISK
    category: AssetCategory = AssetCategory.ANNET
    criticality: int = Field(3, ge=1, le=5)
    location: str | None = None
    ip_address: str | None = None
    serial_number: str | None = None
    manufacturer: str | None = None
    model: str | None = None
    parent_id: int | None = None
    owner_department_id: int | None = None


class AssetCreate(AssetBase):
    """Schema for creating an asset."""

    pass


class AssetUpdate(BaseModel):
    """Schema for updating an asset."""

    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    asset_type: AssetType | None = None
    category: AssetCategory | None = None
    criticality: int | None = Field(None, ge=1, le=5)
    location: str | None = None
    ip_address: str | None = None
    serial_number: str | None = None
    manufacturer: str | None = None
    model: str | None = None
    parent_id: int | None = None
    owner_department_id: int | None = None


class AssetResponse(AssetBase):
    """Schema for asset response."""

    id: int
    netbox_id: int | None = None
    netbox_url: str | None = None
    is_manual: bool = True
    last_synced_at: datetime | None = None
    criticality_label: str = ""
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
