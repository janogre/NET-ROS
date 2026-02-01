"""
Informasjonsverdi-modell for NetROS.
"""

from enum import Enum

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Classification(str, Enum):
    """Klassifisering av informasjon."""

    APEN = "åpen"
    INTERN = "intern"
    FORTROLIG = "fortrolig"
    STRENGT_FORTROLIG = "strengt_fortrolig"


class DataType(str, Enum):
    """Type data som behandles."""

    PERSONOPPLYSNINGER = "personopplysninger"
    DRIFTSDATA = "driftsdata"
    KUNDEDATA = "kundedata"
    FINANSDATA = "finansdata"
    TEKNISK_DOKUMENTASJON = "teknisk_dokumentasjon"
    SIKKERHETSDATA = "sikkerhetsdata"
    ANNET = "annet"


class InformationAsset(Base, TimestampMixin):
    """Informasjonsverdi."""

    __tablename__ = "information_assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    classification: Mapped[Classification] = mapped_column(default=Classification.INTERN)

    # Lagres som komma-separert string for SQLite-kompatibilitet
    data_types_str: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )

    # Eierskap
    owner_department_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.id"), nullable=True
    )

    # Relationships
    owner_department: Mapped["Department | None"] = relationship(
        back_populates="owned_information_assets"
    )
    risk_associations: Mapped[list["InformationAssetRisk"]] = relationship(
        back_populates="information_asset",
        cascade="all, delete-orphan",
    )

    @property
    def data_types(self) -> list[str]:
        """Hent datatyper som liste."""
        if not self.data_types_str:
            return []
        return self.data_types_str.split(",")

    @data_types.setter
    def data_types(self, value: list[str]) -> None:
        """Sett datatyper fra liste."""
        self.data_types_str = ",".join(value) if value else None

    @property
    def classification_label(self) -> str:
        """Norsk label for klassifisering."""
        labels = {
            Classification.APEN: "Åpen",
            Classification.INTERN: "Intern",
            Classification.FORTROLIG: "Fortrolig",
            Classification.STRENGT_FORTROLIG: "Strengt fortrolig",
        }
        return labels.get(self.classification, "Ukjent")


# Import for type hints
from app.models.department import Department
from app.models.risk import InformationAssetRisk
