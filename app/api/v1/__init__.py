"""
API v1 routes for NetROS.
"""

from fastapi import APIRouter

from app.api.v1 import (
    auth,
    assets,
    risks,
    actions,
    projects,
    dashboard,
    reports,
    users,
    suppliers,
    information_assets,
    reviews,
    documents,
    ekomforskriften,
    audit,
    export,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router, prefix="/auth", tags=["Autentisering"])
api_router.include_router(users.router, prefix="/users", tags=["Brukere"])
api_router.include_router(projects.router, prefix="/projects", tags=["Prosjekter"])
api_router.include_router(assets.router, prefix="/assets", tags=["Assets"])
api_router.include_router(suppliers.router, prefix="/suppliers", tags=["Leverandører"])
api_router.include_router(
    information_assets.router, prefix="/information-assets", tags=["Informasjonsverdier"]
)
api_router.include_router(risks.router, prefix="/risks", tags=["Risikoer"])
api_router.include_router(actions.router, prefix="/actions", tags=["Tiltak"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["Gjennomganger"])
api_router.include_router(documents.router, prefix="/documents", tags=["Dokumenter"])
api_router.include_router(
    ekomforskriften.router, prefix="/ekomforskriften", tags=["Ekomforskriften"]
)
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(reports.router, prefix="/reports", tags=["Rapporter"])
api_router.include_router(audit.router, prefix="/audit", tags=["Audit"])
api_router.include_router(export.router, prefix="/export", tags=["Eksport"])
