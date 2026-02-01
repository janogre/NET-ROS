"""
Avdelingsmodell (organisasjonsstruktur) for NetROS.
"""

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Department(Base, TimestampMixin):
    """Organisasjonsenhet/avdeling."""

    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Hierarki (selvreferende)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.id"), nullable=True
    )

    # Leder for avdelingen
    manager_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )

    # Relationships
    parent: Mapped["Department | None"] = relationship(
        "Department",
        back_populates="children",
        remote_side="Department.id",
    )
    children: Mapped[list["Department"]] = relationship(
        "Department",
        back_populates="parent",
    )
    users: Mapped[list["User"]] = relationship(
        back_populates="department",
        foreign_keys="User.department_id",
    )
    manager: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[manager_id],
    )
    owned_assets: Mapped[list["Asset"]] = relationship(back_populates="owner_department")
    owned_risks: Mapped[list["Risk"]] = relationship(
        back_populates="owner_department",
        foreign_keys="Risk.owner_department_id",
    )
    owned_projects: Mapped[list["Project"]] = relationship(
        back_populates="owner_department",
    )
    responsible_actions: Mapped[list["Action"]] = relationship(
        back_populates="responsible_department"
    )
    owned_information_assets: Mapped[list["InformationAsset"]] = relationship(
        back_populates="owner_department"
    )


# Import for type hints
from app.models.user import User
from app.models.asset import Asset
from app.models.risk import Risk
from app.models.project import Project
from app.models.action import Action
from app.models.information_asset import InformationAsset
