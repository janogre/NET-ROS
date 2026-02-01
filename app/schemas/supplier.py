"""
Pydantic schemas for Supplier.
"""

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.supplier import SupplierType


class SupplierBase(BaseModel):
    """Base schema for Supplier."""

    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    supplier_type: SupplierType = SupplierType.TJENESTELEVERANDOR
    criticality: int = Field(3, ge=1, le=5)
    contact_info: str | None = None
    contract_reference: str | None = None
    contract_expiry: date | None = None


class SupplierCreate(SupplierBase):
    """Schema for creating a supplier."""

    pass


class SupplierUpdate(BaseModel):
    """Schema for updating a supplier."""

    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    supplier_type: SupplierType | None = None
    criticality: int | None = Field(None, ge=1, le=5)
    contact_info: str | None = None
    contract_reference: str | None = None
    contract_expiry: date | None = None


class SupplierResponse(SupplierBase):
    """Schema for supplier response."""

    id: int
    criticality_label: str = ""
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
