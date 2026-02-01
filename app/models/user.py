"""
Brukermodell med RBAC for NetROS.
"""

from enum import Enum

from sqlalchemy import ForeignKey, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class UserRole(str, Enum):
    """Brukerroller med tilhørende rettigheter."""

    ADMIN = "admin"  # Full tilgang, brukeradministrasjon
    RISIKOANSVARLIG = "risikoansvarlig"  # CRUD alle risikoer/tiltak
    BRUKER = "bruker"  # Opprette/redigere egne risikoer
    LESER = "leser"  # Kun lesetilgang


class User(Base, TimestampMixin):
    """Bruker i systemet."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(default=UserRole.BRUKER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Tilhører en avdeling
    department_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.id"), nullable=True
    )

    # Relationships
    department: Mapped["Department"] = relationship(
        back_populates="users",
        foreign_keys=[department_id],
    )
    owned_risks: Mapped[list["Risk"]] = relationship(
        back_populates="owner", foreign_keys="Risk.owner_id"
    )
    assigned_actions: Mapped[list["Action"]] = relationship(back_populates="assignee")
    conducted_reviews: Mapped[list["Review"]] = relationship(back_populates="conductor")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="user")

    def has_permission(self, permission: str) -> bool:
        """Sjekk om brukeren har en bestemt tilgang."""
        permissions = {
            UserRole.ADMIN: ["*"],
            UserRole.RISIKOANSVARLIG: [
                "read", "write", "delete", "approve", "report"
            ],
            UserRole.BRUKER: ["read", "write_own", "report"],
            UserRole.LESER: ["read"],
        }
        user_perms = permissions.get(self.role, [])
        return "*" in user_perms or permission in user_perms


# Import for type hints
from app.models.department import Department
from app.models.risk import Risk
from app.models.action import Action
from app.models.review import Review
from app.models.audit import AuditLog
