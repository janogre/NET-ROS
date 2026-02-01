"""
Konfigurasjon for NetROS-applikasjonen.
Leser verdier fra miljøvariabler (.env-fil).
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Applikasjonskonfigurasjon."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    database_url: str = "sqlite+aiosqlite:///./netros.db"

    # Sikkerhet
    secret_key: str = "dev-secret-key-endre-i-produksjon"
    access_token_expire_minutes: int = 480
    session_expire_hours: int = 8
    algorithm: str = "HS256"

    # Applikasjon
    app_name: str = "NetROS"
    app_version: str = "0.1.0"
    debug: bool = True
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # Netbox (Fase 2)
    netbox_url: str | None = None
    netbox_token: str | None = None
    netbox_sync_interval_hours: int = 24

    # Rapport-innstillinger
    company_name: str = "NEAS AS"
    company_org_nr: str = ""

    @property
    def is_sqlite(self) -> bool:
        """Sjekk om databasen er SQLite."""
        return "sqlite" in self.database_url.lower()


@lru_cache
def get_settings() -> Settings:
    """Hent cached settings-instans."""
    return Settings()


settings = get_settings()
