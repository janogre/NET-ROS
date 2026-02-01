"""
Ekomforskriften-modell for NetROS.
Forskrift om elektronisk kommunikasjonsnett og elektronisk kommunikasjonstjeneste.
"""

from enum import Enum

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class EkomCategory(str, Enum):
    """Ekomforskriften hovedkategorier."""

    SIKKERHET = "Sikkerhet og beredskap"
    KONFIDENSIALITET = "Konfidensialitet"
    DOKUMENTASJON = "Dokumentasjon"
    VARSLING = "Varsling"


class EkomParagraph(str, Enum):
    """Ekomforskriften relevante paragrafer for ROS-analyse."""

    # Kapittel 2: Sikkerhet og beredskap
    PARA_2_1 = "2-1"   # Krav om sikkerhet
    PARA_2_2 = "2-2"   # Sikkerhetstiltak
    PARA_2_3 = "2-3"   # Sikkerhetsgodkjenning
    PARA_2_4 = "2-4"   # Beredskap
    PARA_2_5 = "2-5"   # Konfidensialitet
    PARA_2_6 = "2-6"   # Risiko- og sårbarhetsanalyser
    PARA_2_7 = "2-7"   # Varslingsplikt
    PARA_2_8 = "2-8"   # Dokumentasjonsplikt

    # Andre relevante paragrafer
    PARA_2_9 = "2-9"   # Tilsyn
    PARA_2_10 = "2-10"  # Pålegg


class EkomPrinciple(Base, TimestampMixin):
    """Ekomforskriften prinsipp/paragraf (referansedata)."""

    __tablename__ = "ekom_principles"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    paragraph: Mapped[EkomParagraph] = mapped_column(index=True)
    category: Mapped[EkomCategory]
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    legal_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    risk_mappings: Mapped[list["EkomMapping"]] = relationship(
        back_populates="ekom_principle"
    )
    action_mappings: Mapped[list["EkomActionMapping"]] = relationship(
        back_populates="ekom_principle"
    )

    @property
    def full_code(self) -> str:
        """Full kode med ekomforskriften-prefix."""
        return f"Ekomforskriften § {self.code}"

    @property
    def category_label(self) -> str:
        """Norsk label for kategori."""
        return self.category.value


class EkomMapping(Base, TimestampMixin):
    """Kobling mellom Risk og Ekomforskriften-prinsipp."""

    __tablename__ = "ekom_mappings"

    id: Mapped[int] = mapped_column(primary_key=True)
    risk_id: Mapped[int] = mapped_column(ForeignKey("risks.id"), index=True)
    ekom_principle_id: Mapped[int] = mapped_column(
        ForeignKey("ekom_principles.id"), index=True
    )
    compliance_status: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # "compliant", "partial", "non_compliant", "not_assessed"
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    risk: Mapped["Risk"] = relationship(back_populates="ekom_mappings")
    ekom_principle: Mapped["EkomPrinciple"] = relationship(back_populates="risk_mappings")


class EkomActionMapping(Base, TimestampMixin):
    """Kobling mellom Action og Ekomforskriften-prinsipp."""

    __tablename__ = "ekom_action_mappings"

    id: Mapped[int] = mapped_column(primary_key=True)
    action_id: Mapped[int] = mapped_column(ForeignKey("actions.id"), index=True)
    ekom_principle_id: Mapped[int] = mapped_column(
        ForeignKey("ekom_principles.id"), index=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    action: Mapped["Action"] = relationship(back_populates="ekom_mappings")
    ekom_principle: Mapped["EkomPrinciple"] = relationship(back_populates="action_mappings")


# Import for type hints
from app.models.risk import Risk
from app.models.action import Action
