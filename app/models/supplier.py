"""
Leverandørmodell for NetROS.
"""

from datetime import date
from enum import Enum

from sqlalchemy import Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class SupplierType(str, Enum):
    """Type leverandør."""

    UTSTYRSLEVERANDOR = "utstyrsleverandør"
    TJENESTELEVERANDOR = "tjenesteleverandør"
    UNDERLEVERANDOR = "underleverandør"


class Supplier(Base, TimestampMixin):
    """Leverandør."""

    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    supplier_type: Mapped[SupplierType] = mapped_column(
        default=SupplierType.TJENESTELEVERANDOR
    )
    criticality: Mapped[int] = mapped_column(Integer, default=3)  # 1-5

    # Kontaktinfo
    contact_info: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Kontrakt
    contract_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    contract_expiry: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Relationships
    asset_associations: Mapped[list["AssetSupplier"]] = relationship(
        back_populates="supplier",
        cascade="all, delete-orphan",
    )

    @property
    def criticality_label(self) -> str:
        """Norsk label for kritikalitet."""
        labels = {
            1: "Svært lav",
            2: "Lav",
            3: "Middels",
            4: "Høy",
            5: "Kritisk",
        }
        return labels.get(self.criticality, "Ukjent")


class AssetSupplier(Base, TimestampMixin):
    """Kobling mellom Asset og Supplier."""

    __tablename__ = "asset_suppliers"

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), index=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"), index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    asset: Mapped["Asset"] = relationship(back_populates="supplier_associations")
    supplier: Mapped["Supplier"] = relationship(back_populates="asset_associations")


# Import for type hints
from app.models.asset import Asset
