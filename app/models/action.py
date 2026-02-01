"""
Tiltaksmodell for NetROS.
"""

from datetime import date, datetime
from enum import Enum

from sqlalchemy import Date, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class ActionPriority(str, Enum):
    """Prioritet for tiltak."""

    LAV = "lav"
    MIDDELS = "middels"
    HOY = "høy"
    KRITISK = "kritisk"


class ActionStatus(str, Enum):
    """Status for tiltak."""

    PLANLAGT = "planlagt"
    PAGAENDE = "pågår"
    FULLFORT = "fullført"
    AVBRUTT = "avbrutt"
    FORFALT = "forfalt"


class Action(Base, TimestampMixin):
    """Tiltak for risikoreduksjon."""

    __tablename__ = "actions"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(300), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[ActionPriority] = mapped_column(default=ActionPriority.MIDDELS)
    status: Mapped[ActionStatus] = mapped_column(default=ActionStatus.PLANLAGT)

    # Datoer
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Ansvarlig
    assignee_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    responsible_department_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.id"), nullable=True
    )

    # Relationships
    assignee: Mapped["User | None"] = relationship(back_populates="assigned_actions")
    responsible_department: Mapped["Department | None"] = relationship(
        back_populates="responsible_actions"
    )
    risk_associations: Mapped[list["RiskAction"]] = relationship(
        back_populates="action",
        cascade="all, delete-orphan",
    )
    ekom_mappings: Mapped[list["EkomActionMapping"]] = relationship(
        back_populates="action",
        cascade="all, delete-orphan",
    )

    @property
    def is_overdue(self) -> bool:
        """Sjekk om tiltaket er forfalt."""
        if self.status == ActionStatus.FULLFORT:
            return False
        if self.due_date is None:
            return False
        return date.today() > self.due_date

    @property
    def priority_label(self) -> str:
        """Norsk label for prioritet."""
        labels = {
            ActionPriority.LAV: "Lav",
            ActionPriority.MIDDELS: "Middels",
            ActionPriority.HOY: "Høy",
            ActionPriority.KRITISK: "Kritisk",
        }
        return labels.get(self.priority, "Ukjent")

    @property
    def status_label(self) -> str:
        """Norsk label for status."""
        labels = {
            ActionStatus.PLANLAGT: "Planlagt",
            ActionStatus.PAGAENDE: "Pågår",
            ActionStatus.FULLFORT: "Fullført",
            ActionStatus.AVBRUTT: "Avbrutt",
            ActionStatus.FORFALT: "Forfalt",
        }
        return labels.get(self.status, "Ukjent")


class RiskAction(Base, TimestampMixin):
    """Kobling mellom Risk og Action."""

    __tablename__ = "risk_actions"

    id: Mapped[int] = mapped_column(primary_key=True)
    risk_id: Mapped[int] = mapped_column(ForeignKey("risks.id"), index=True)
    action_id: Mapped[int] = mapped_column(ForeignKey("actions.id"), index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    risk: Mapped["Risk"] = relationship(back_populates="action_associations")
    action: Mapped["Action"] = relationship(back_populates="risk_associations")


# Import for type hints
from app.models.user import User
from app.models.department import Department
from app.models.risk import Risk
from app.models.ekomforskriften import EkomActionMapping
