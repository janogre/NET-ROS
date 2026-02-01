"""
Prosjektmodell for ROS-analyser.
"""

from datetime import date
from enum import Enum

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class ProjectType(str, Enum):
    """Type ROS-prosjekt."""

    PERIODISK_ROS = "periodisk_ros"  # Årlig/periodisk analyse
    HENDELSESBASERT = "hendelsesbasert"  # Etter hendelse
    DPIA = "dpia"  # Personvernkonsekvensanalyse
    ENDRING = "endring"  # Ved større endringer


class ProjectStatus(str, Enum):
    """Status for prosjekt."""

    PLANLAGT = "planlagt"
    PAGAENDE = "pågår"
    FULLFORT = "fullført"


class Project(Base, TimestampMixin):
    """ROS-prosjekt som samler risikovurderinger."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    project_type: Mapped[ProjectType] = mapped_column(default=ProjectType.PERIODISK_ROS)
    status: Mapped[ProjectStatus] = mapped_column(default=ProjectStatus.PLANLAGT)

    # Datoer
    scheduled_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    completed_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Eierskap
    owner_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    owner_department_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.id"), nullable=True
    )

    # Relationships
    owner: Mapped["User | None"] = relationship("User")
    owner_department: Mapped["Department | None"] = relationship(
        back_populates="owned_projects"
    )
    risks: Mapped[list["Risk"]] = relationship(back_populates="project")


# Import for type hints
from app.models.user import User
from app.models.department import Department
from app.models.risk import Risk
