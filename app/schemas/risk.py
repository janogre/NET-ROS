"""
Pydantic schemas for Risk.
"""

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.risk import RiskType, RiskStatus


class RiskBase(BaseModel):
    """Base schema for Risk."""

    title: str = Field(..., min_length=1, max_length=300)
    description: str | None = None
    risk_type: RiskType = RiskType.TEKNISK
    project_id: int | None = None
    likelihood: int = Field(3, ge=1, le=5)
    consequence: int = Field(3, ge=1, le=5)
    target_likelihood: int | None = Field(None, ge=1, le=5)
    target_consequence: int | None = Field(None, ge=1, le=5)
    status: RiskStatus = RiskStatus.IDENTIFISERT
    owner_id: int | None = None
    owner_department_id: int | None = None
    vulnerability_description: str | None = None
    threat_description: str | None = None
    existing_controls: str | None = None
    proposed_measures: str | None = None
    next_review_date: date | None = None


class RiskCreate(RiskBase):
    """Schema for creating a risk."""

    asset_ids: list[int] = []
    nsm_principle_ids: list[int] = []


class RiskUpdate(BaseModel):
    """Schema for updating a risk."""

    title: str | None = Field(None, min_length=1, max_length=300)
    description: str | None = None
    risk_type: RiskType | None = None
    project_id: int | None = None
    likelihood: int | None = Field(None, ge=1, le=5)
    consequence: int | None = Field(None, ge=1, le=5)
    target_likelihood: int | None = Field(None, ge=1, le=5)
    target_consequence: int | None = Field(None, ge=1, le=5)
    status: RiskStatus | None = None
    owner_id: int | None = None
    owner_department_id: int | None = None
    vulnerability_description: str | None = None
    threat_description: str | None = None
    existing_controls: str | None = None
    proposed_measures: str | None = None
    next_review_date: date | None = None
    asset_ids: list[int] | None = None
    nsm_principle_ids: list[int] | None = None


class RiskResponse(RiskBase):
    """Schema for risk response."""

    id: int
    risk_score: int
    target_risk_score: int | None = None
    risk_level: str
    risk_color: str
    project_name: str | None = None
    last_reviewed_at: date | None = None
    # Acceptance fields
    accepted_by_id: int | None = None
    accepted_at: datetime | None = None
    acceptance_rationale: str | None = None
    acceptance_valid_until: date | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RiskAcceptRequest(BaseModel):
    """Schema for accepting a risk."""

    rationale: str = Field(..., min_length=10, max_length=2000, description="Begrunnelse for aksept")
    valid_until: date | None = Field(None, description="Akseptansen gjelder til denne datoen")


class RiskAcceptResponse(BaseModel):
    """Schema for risk acceptance response."""

    id: int
    title: str
    status: RiskStatus
    accepted_by_id: int
    accepted_at: datetime
    acceptance_rationale: str
    acceptance_valid_until: date | None
    message: str = "Risiko akseptert"

    model_config = {"from_attributes": True}


class RiskSummary(BaseModel):
    """Enkel risikoinfo for matrise-tooltip."""

    id: int
    title: str
    project_name: str | None = None


class RiskMatrixCell(BaseModel):
    """En celle i risikomatrisen."""

    likelihood: int
    consequence: int
    score: int
    color: str
    risk_ids: list[int] = []
    risk_count: int = 0
    risks: list[RiskSummary] = []


class RiskMatrix(BaseModel):
    """Komplett risikomatrise."""

    cells: list[list[RiskMatrixCell]]
    total_risks: int = 0
