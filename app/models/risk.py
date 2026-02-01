"""
Risikomodell med matrise-beregning for NetROS.
"""

from datetime import date
from enum import Enum

from sqlalchemy import Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class RiskType(str, Enum):
    """Type risiko."""

    TEKNISK = "teknisk"
    OPERASJONELL = "operasjonell"
    ORGANISATORISK = "organisatorisk"
    EKSTERN = "ekstern"
    NATURHENDELSE = "naturhendelse"


class RiskStatus(str, Enum):
    """Status for risiko."""

    IDENTIFISERT = "identifisert"
    UNDER_VURDERING = "under_vurdering"
    AKSEPTERT = "akseptert"
    REDUSERT = "redusert"
    OVERFORT = "overført"
    LUKKET = "lukket"


class Risk(Base, TimestampMixin):
    """Risiko i ROS-analysen."""

    __tablename__ = "risks"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(300), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_type: Mapped[RiskType] = mapped_column(default=RiskType.TEKNISK)

    # Prosjekttilhørighet
    project_id: Mapped[int | None] = mapped_column(
        ForeignKey("projects.id"), nullable=True, index=True
    )

    # Nåværende risikovurdering
    likelihood: Mapped[int] = mapped_column(Integer, default=3)  # 1-5
    consequence: Mapped[int] = mapped_column(Integer, default=3)  # 1-5

    # Mål-risikovurdering (etter tiltak)
    target_likelihood: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target_consequence: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Status
    status: Mapped[RiskStatus] = mapped_column(default=RiskStatus.IDENTIFISERT)

    # Eierskap
    owner_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    owner_department_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.id"), nullable=True
    )

    # Beskrivelser
    vulnerability_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    threat_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    existing_controls: Mapped[str | None] = mapped_column(Text, nullable=True)
    proposed_measures: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Gjennomgang
    last_reviewed_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    next_review_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Relationships
    project: Mapped["Project | None"] = relationship(back_populates="risks")
    owner: Mapped["User | None"] = relationship(
        back_populates="owned_risks",
        foreign_keys=[owner_id],
    )
    owner_department: Mapped["Department | None"] = relationship(
        back_populates="owned_risks",
        foreign_keys=[owner_department_id],
    )
    asset_associations: Mapped[list["AssetRisk"]] = relationship(
        back_populates="risk",
        cascade="all, delete-orphan",
    )
    action_associations: Mapped[list["RiskAction"]] = relationship(
        back_populates="risk",
        cascade="all, delete-orphan",
    )
    nsm_mappings: Mapped[list["NSMMapping"]] = relationship(
        back_populates="risk",
        cascade="all, delete-orphan",
    )
    review_associations: Mapped[list["ReviewRisk"]] = relationship(
        back_populates="risk",
        cascade="all, delete-orphan",
    )
    information_asset_associations: Mapped[list["InformationAssetRisk"]] = relationship(
        back_populates="risk",
        cascade="all, delete-orphan",
    )
    ekom_mappings: Mapped[list["EkomMapping"]] = relationship(
        back_populates="risk",
        cascade="all, delete-orphan",
    )

    @property
    def risk_score(self) -> int:
        """Beregn nåværende risikoscore."""
        return self.likelihood * self.consequence

    @property
    def target_risk_score(self) -> int | None:
        """Beregn mål-risikoscore (etter tiltak)."""
        if self.target_likelihood is None or self.target_consequence is None:
            return None
        return self.target_likelihood * self.target_consequence

    @property
    def risk_level(self) -> str:
        """Norsk risikonivå basert på score."""
        score = self.risk_score
        if score <= 4:
            return "Akseptabel"
        elif score <= 9:
            return "Lav"
        elif score <= 16:
            return "Middels"
        else:
            return "Høy"

    @property
    def risk_color(self) -> str:
        """CSS-farge for risikonivå."""
        score = self.risk_score
        if score <= 4:
            return "green"
        elif score <= 9:
            return "yellow"
        elif score <= 16:
            return "orange"
        else:
            return "red"

    @property
    def project_name(self) -> str | None:
        """Prosjektnavn fra relasjon."""
        if self.project:
            return self.project.name
        return None

    @staticmethod
    def likelihood_label(value: int) -> str:
        """Norsk label for sannsynlighet."""
        labels = {
            1: "Svært lav",
            2: "Lav",
            3: "Middels",
            4: "Høy",
            5: "Svært høy",
        }
        return labels.get(value, "Ukjent")

    @staticmethod
    def consequence_label(value: int) -> str:
        """Norsk label for konsekvens."""
        labels = {
            1: "Svært lav",
            2: "Lav",
            3: "Middels",
            4: "Høy",
            5: "Svært høy",
        }
        return labels.get(value, "Ukjent")


class AssetRisk(Base, TimestampMixin):
    """Kobling mellom Asset og Risk."""

    __tablename__ = "asset_risks"

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), index=True)
    risk_id: Mapped[int] = mapped_column(ForeignKey("risks.id"), index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    asset: Mapped["Asset"] = relationship(back_populates="risk_associations")
    risk: Mapped["Risk"] = relationship(back_populates="asset_associations")


class NSMMapping(Base, TimestampMixin):
    """Kobling mellom Risk og NSM-prinsipp."""

    __tablename__ = "nsm_mappings"

    id: Mapped[int] = mapped_column(primary_key=True)
    risk_id: Mapped[int] = mapped_column(ForeignKey("risks.id"), index=True)
    nsm_principle_id: Mapped[int] = mapped_column(
        ForeignKey("nsm_principles.id"), index=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    risk: Mapped["Risk"] = relationship(back_populates="nsm_mappings")
    nsm_principle: Mapped["NSMPrinciple"] = relationship(back_populates="risk_mappings")


class InformationAssetRisk(Base, TimestampMixin):
    """Kobling mellom InformationAsset og Risk."""

    __tablename__ = "information_asset_risks"

    id: Mapped[int] = mapped_column(primary_key=True)
    information_asset_id: Mapped[int] = mapped_column(
        ForeignKey("information_assets.id"), index=True
    )
    risk_id: Mapped[int] = mapped_column(ForeignKey("risks.id"), index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    information_asset: Mapped["InformationAsset"] = relationship(
        back_populates="risk_associations"
    )
    risk: Mapped["Risk"] = relationship(
        back_populates="information_asset_associations"
    )


# Import for type hints
from app.models.project import Project
from app.models.user import User
from app.models.department import Department
from app.models.asset import Asset
from app.models.action import RiskAction
from app.models.nsm import NSMPrinciple
from app.models.review import ReviewRisk
from app.models.information_asset import InformationAsset
from app.models.ekomforskriften import EkomMapping
