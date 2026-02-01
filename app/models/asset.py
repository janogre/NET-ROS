"""
Asset-modell (verdier/enheter) for NetROS.
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, String, Text, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class AssetCategory(str, Enum):
    """Kategorier for assets (telekom-spesifikke)."""

    KJERNENETT = "kjernenett"
    AKSESSNETT = "aksessnett"
    RADIOSONE = "radiosone"
    KUNDESEGMENT = "kundesegment"
    DATASENTER = "datasenter"
    TRANSPORT = "transport"
    KRAFT = "kraft"
    ANNET = "annet"


class AssetType(str, Enum):
    """Type asset."""

    FYSISK = "fysisk"  # Hardware, utstyr
    VIRTUELL = "virtuell"  # VM, container
    TJENESTE = "tjeneste"  # Applikasjon, system
    NETTVERK = "nettverk"  # Nettverkssegment
    LOKASJON = "lokasjon"  # Site, bygning


class Asset(Base, TimestampMixin):
    """Asset/verdi i infrastrukturen."""

    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    asset_type: Mapped[AssetType] = mapped_column(default=AssetType.FYSISK)
    category: Mapped[AssetCategory] = mapped_column(default=AssetCategory.ANNET)
    criticality: Mapped[int] = mapped_column(Integer, default=3)  # 1-5

    # Netbox-integrasjon
    netbox_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    netbox_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_manual: Mapped[bool] = mapped_column(Boolean, default=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Tekniske detaljer
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)
    serial_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    manufacturer: Mapped[str | None] = mapped_column(String(100), nullable=True)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Hierarki
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("assets.id"), nullable=True
    )

    # Eierskap
    owner_department_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.id"), nullable=True
    )

    # Relationships
    parent: Mapped["Asset | None"] = relationship(
        "Asset",
        back_populates="children",
        remote_side="Asset.id",
    )
    children: Mapped[list["Asset"]] = relationship(
        "Asset",
        back_populates="parent",
    )
    owner_department: Mapped["Department | None"] = relationship(
        back_populates="owned_assets"
    )
    risk_associations: Mapped[list["AssetRisk"]] = relationship(
        back_populates="asset",
        cascade="all, delete-orphan",
    )
    supplier_associations: Mapped[list["AssetSupplier"]] = relationship(
        back_populates="asset",
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


# Import for type hints
from app.models.department import Department
from app.models.risk import AssetRisk
from app.models.supplier import AssetSupplier
