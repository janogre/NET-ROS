"""
NSM Grunnprinsipper modell for NetROS.
"""

from datetime import date
from enum import Enum

from sqlalchemy import Date, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class NSMCategory(str, Enum):
    """NSM-kategorier (Grunnprinsipper for IKT-sikkerhet)."""

    IDENTIFISERE = "1. Identifisere"
    BESKYTTE = "2. Beskytte"
    OPPDAGE = "3. Oppdage"
    HANDTERE = "4. Håndtere og gjenopprette"


class NSMPrinciple(Base):
    """NSM Grunnprinsipp (referansedata)."""

    __tablename__ = "nsm_principles"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    category: Mapped[NSMCategory]
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    # Versjonering
    version: Mapped[str] = mapped_column(String(20), default="2.0", server_default="2.0")
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    deprecated_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Relationships
    risk_mappings: Mapped[list["NSMMapping"]] = relationship(
        back_populates="nsm_principle"
    )

    @property
    def full_code(self) -> str:
        """Full kode med kategori-prefix."""
        return f"{self.code}"

    @property
    def category_label(self) -> str:
        """Norsk label for kategori."""
        return self.category.value

    @property
    def is_deprecated(self) -> bool:
        """Sjekk om prinsippet er utgått."""
        if self.deprecated_date is None:
            return False
        return self.deprecated_date <= date.today()

    @property
    def is_active(self) -> bool:
        """Sjekk om prinsippet er aktivt (gyldig og ikke utgått)."""
        today = date.today()
        if self.effective_date and self.effective_date > today:
            return False
        return not self.is_deprecated


# Import for type hints
from app.models.risk import NSMMapping
