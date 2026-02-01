"""
Report endpoints for NetROS.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user
from app.database import get_db
from app.models.user import User
from app.services.report_service import ReportService
from app.services.risk_service import RiskService

router = APIRouter()


@router.get("/risk-register")
async def get_risk_register_html(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_active_user)],
    project_id: int | None = None,
) -> Response:
    """Hent risikoregister som HTML."""
    report_service = ReportService(db)
    html = await report_service.generate_risk_register_html(project_id)
    return Response(content=html, media_type="text/html")


@router.get("/risk-register/pdf")
async def get_risk_register_pdf(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_active_user)],
    project_id: int | None = None,
) -> Response:
    """Hent risikoregister som PDF."""
    report_service = ReportService(db)
    pdf = await report_service.generate_risk_register_pdf(project_id)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=risikoregister.pdf"},
    )


@router.get("/nkom-summary")
async def get_nkom_summary_html(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_active_user)],
    project_id: int | None = None,
) -> Response:
    """Hent Nkom-sammendrag som HTML."""
    report_service = ReportService(db)
    html = await report_service.generate_nkom_summary_html(project_id)
    return Response(content=html, media_type="text/html")


@router.post("/nkom-summary/pdf")
async def get_nkom_summary_pdf(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_active_user)],
    project_id: int | None = None,
) -> Response:
    """Hent Nkom-sammendrag som PDF."""
    report_service = ReportService(db)
    pdf = await report_service.generate_nkom_summary_pdf(project_id)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=nkom-sammendrag.pdf"},
    )


@router.get("/risk-matrix")
async def get_risk_matrix_report(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_active_user)],
    project_id: int | None = None,
) -> dict:
    """Hent risikomatrise-data for rapport."""
    risk_service = RiskService(db)
    current_matrix = await risk_service.get_risk_matrix(project_id)
    target_matrix = await risk_service.get_target_risk_matrix(project_id)

    return {
        "current_matrix": current_matrix.model_dump(),
        "target_matrix": target_matrix.model_dump(),
    }


@router.get("/nsm-coverage")
async def get_nsm_coverage_report(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """Hent NSM-dekningsrapport."""
    risk_service = RiskService(db)
    return await risk_service.get_nsm_coverage()
