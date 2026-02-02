"""
Export endpoints for NetROS.
Provides Excel export functionality for risks, actions, assets, and coverage reports.
"""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user
from app.database import get_db
from app.models.user import User
from app.services.export_service import ExportService
from app.services.audit_service import AuditService

router = APIRouter()


def _get_export_filename(base_name: str) -> str:
    """Generate filename with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{base_name}_{timestamp}.xlsx"


@router.get("/risks")
async def export_risks(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    project_id: int | None = Query(None, description="Filtrer på prosjekt-ID"),
) -> StreamingResponse:
    """
    Eksporter risikoer til Excel.

    Returnerer en xlsx-fil med alle risikoer, inkludert:
    - Risikoinformasjon (tittel, beskrivelse, type)
    - Risikomatrise-verdier (sannsynlighet, konsekvens, score)
    - Status og eierskap
    - Akseptanseinformasjon (hvis akseptert)
    """
    export_service = ExportService(db)
    buffer = await export_service.export_risks(project_id)

    # Log export
    audit_service = AuditService(db)
    await audit_service.log_export(
        entity_type="risks",
        user=current_user,
        export_format="xlsx",
    )
    await db.commit()

    filename = _get_export_filename("risikoer")
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/actions")
async def export_actions(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> StreamingResponse:
    """
    Eksporter tiltak til Excel.

    Returnerer en xlsx-fil med alle tiltak, inkludert:
    - Tiltaksinformasjon (tittel, beskrivelse)
    - Prioritet og status
    - Frist og ansvarlig
    - Fullføringsdato
    """
    export_service = ExportService(db)
    buffer = await export_service.export_actions()

    # Log export
    audit_service = AuditService(db)
    await audit_service.log_export(
        entity_type="actions",
        user=current_user,
        export_format="xlsx",
    )
    await db.commit()

    filename = _get_export_filename("tiltak")
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/assets")
async def export_assets(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    category: str | None = Query(None, description="Filtrer på kategori"),
) -> StreamingResponse:
    """
    Eksporter assets til Excel.

    Returnerer en xlsx-fil med alle assets, inkludert:
    - Asset-informasjon (navn, beskrivelse, type)
    - Kategori og kritikalitet
    - Teknisk informasjon (IP, serienummer, etc.)
    """
    export_service = ExportService(db)
    buffer = await export_service.export_assets(category)

    # Log export
    audit_service = AuditService(db)
    await audit_service.log_export(
        entity_type="assets",
        user=current_user,
        export_format="xlsx",
    )
    await db.commit()

    filename = _get_export_filename("assets")
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/coverage")
async def export_coverage_report(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> StreamingResponse:
    """
    Eksporter dekningsrapport til Excel.

    Returnerer en xlsx-fil med:
    - NSM Grunnprinsipper med dekningsstatus
    - Ekomforskriften-paragrafer med dekningsstatus
    - Sammendrag med dekningsgrad per rammeverk
    """
    export_service = ExportService(db)
    buffer = await export_service.export_coverage_report()

    # Log export
    audit_service = AuditService(db)
    await audit_service.log_export(
        entity_type="coverage_report",
        user=current_user,
        export_format="xlsx",
    )
    await db.commit()

    filename = _get_export_filename("dekningsrapport")
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
