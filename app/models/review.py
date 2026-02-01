"""
Gjennomgangsmodell for NetROS.
"""

from datetime import date
from enum import Enum

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class ReviewType(str, Enum):
    """Type gjennomgang."""

    PERIODISK = "periodisk"
    HENDELSE = "hendelse"
    ENDRING = "endring"
    REVISJON = "revisjon"


class Review(Base, TimestampMixin):
    """Gjennomgang av risikoer."""

    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(300), index=True)
    review_type: Mapped[ReviewType] = mapped_column(default=ReviewType.PERIODISK)

    # Datoer
    scheduled_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    conducted_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    next_review_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Gjennomfører
    conductor_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )

    # Funn og konklusjoner
    findings: Mapped[str | None] = mapped_column(Text, nullable=True)
    conclusions: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Hendelsesreferanse (for hendelsesbaserte)
    incident_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    incident_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Relationships
    conductor: Mapped["User | None"] = relationship(back_populates="conducted_reviews")
    risk_associations: Mapped[list["ReviewRisk"]] = relationship(
        back_populates="review",
        cascade="all, delete-orphan",
    )

    @property
    def is_completed(self) -> bool:
        """Sjekk om gjennomgangen er fullført."""
        return self.conducted_date is not None

    @property
    def review_type_label(self) -> str:
        """Norsk label for gjennomgangstype."""
        labels = {
            ReviewType.PERIODISK: "Periodisk",
            ReviewType.HENDELSE: "Hendelsesbasert",
            ReviewType.ENDRING: "Endringsbasert",
            ReviewType.REVISJON: "Revisjon",
        }
        return labels.get(self.review_type, "Ukjent")


class ReviewRisk(Base, TimestampMixin):
    """Kobling mellom Review og Risk."""

    __tablename__ = "review_risks"

    id: Mapped[int] = mapped_column(primary_key=True)
    review_id: Mapped[int] = mapped_column(ForeignKey("reviews.id"), index=True)
    risk_id: Mapped[int] = mapped_column(ForeignKey("risks.id"), index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    review: Mapped["Review"] = relationship(back_populates="risk_associations")
    risk: Mapped["Risk"] = relationship(back_populates="review_associations")


# Import for type hints
from app.models.user import User
from app.models.risk import Risk
