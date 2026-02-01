"""
Pydantic schemas for Ekomforskriften.
"""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.ekomforskriften import EkomCategory, EkomParagraph


class ComplianceStatus(str):
    """Samsvarsstatus for ekomforskriften-krav."""

    COMPLIANT = "compliant"
    PARTIAL = "partial"
    NON_COMPLIANT = "non_compliant"
    NOT_ASSESSED = "not_assessed"


class EkomPrincipleBase(BaseModel):
    """Base schema for EkomPrinciple."""

    code: str = Field(..., min_length=1, max_length=20)
    paragraph: EkomParagraph
    category: EkomCategory
    title: str = Field(..., min_length=1, max_length=300)
    description: str | None = None
    legal_text: str | None = None
    sort_order: int = 0


class EkomPrincipleCreate(EkomPrincipleBase):
    """Schema for creating an Ekomforskriften principle."""

    pass


class EkomPrincipleUpdate(BaseModel):
    """Schema for updating an Ekomforskriften principle."""

    code: str | None = Field(None, min_length=1, max_length=20)
    paragraph: EkomParagraph | None = None
    category: EkomCategory | None = None
    title: str | None = Field(None, min_length=1, max_length=300)
    description: str | None = None
    legal_text: str | None = None
    sort_order: int | None = None


class EkomPrincipleResponse(EkomPrincipleBase):
    """Schema for Ekomforskriften principle response."""

    id: int
    full_code: str = ""
    category_label: str = ""
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EkomMappingBase(BaseModel):
    """Base schema for EkomMapping."""

    risk_id: int
    ekom_principle_id: int
    compliance_status: str | None = None
    notes: str | None = None


class EkomMappingCreate(EkomMappingBase):
    """Schema for creating an EkomMapping."""

    pass


class EkomMappingUpdate(BaseModel):
    """Schema for updating an EkomMapping."""

    compliance_status: str | None = None
    notes: str | None = None


class EkomMappingResponse(EkomMappingBase):
    """Schema for EkomMapping response."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EkomMappingWithPrincipleResponse(EkomMappingResponse):
    """Schema for EkomMapping with principle details."""

    principle_code: str = ""
    principle_title: str = ""
    principle_category: str = ""


class EkomActionMappingBase(BaseModel):
    """Base schema for EkomActionMapping."""

    action_id: int
    ekom_principle_id: int
    notes: str | None = None


class EkomActionMappingCreate(EkomActionMappingBase):
    """Schema for creating an EkomActionMapping."""

    pass


class EkomActionMappingResponse(EkomActionMappingBase):
    """Schema for EkomActionMapping response."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EkomComplianceSummary(BaseModel):
    """Sammendrag av ekomforskriften-samsvar."""

    total_principles: int = 0
    risks_with_mapping: int = 0
    compliant: int = 0
    partial: int = 0
    non_compliant: int = 0
    not_assessed: int = 0
    coverage_percentage: float = 0.0


class EkomComplianceByCategory(BaseModel):
    """Samsvar per kategori."""

    category: str
    category_label: str
    total: int = 0
    compliant: int = 0
    partial: int = 0
    non_compliant: int = 0
    not_assessed: int = 0
