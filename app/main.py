"""
FastAPI entry point for NetROS.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.v1 import api_router
from app.config import settings
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events for the application."""
    # Startup
    await init_db()
    yield
    # Shutdown


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="ROS-analyseverktøy for NEAS - Risiko og sårbarhetsanalyse",
    lifespan=lifespan,
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include API router
app.include_router(api_router)

# Templates
templates = Jinja2Templates(directory="app/templates")


# Web routes (server-side rendering)
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Redirect to dashboard or login."""
    token = request.cookies.get("access_token")
    if token:
        return RedirectResponse(url="/dashboard", status_code=302)
    return RedirectResponse(url="/login", status_code=302)


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page."""
    return templates.TemplateResponse(
        "pages/login.html",
        {"request": request, "title": "Logg inn"},
    )


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """Dashboard page."""
    return templates.TemplateResponse(
        "pages/dashboard.html",
        {"request": request, "title": "Dashboard"},
    )


@app.get("/prosjekter", response_class=HTMLResponse)
async def projects_page(request: Request):
    """Projects list page."""
    return templates.TemplateResponse(
        "pages/projects/list.html",
        {"request": request, "title": "Prosjekter"},
    )


@app.get("/prosjekter/{project_id}", response_class=HTMLResponse)
async def project_detail_page(request: Request, project_id: int):
    """Project detail page."""
    return templates.TemplateResponse(
        "pages/projects/detail.html",
        {"request": request, "title": "Prosjekt", "project_id": project_id},
    )


@app.get("/assets", response_class=HTMLResponse)
async def assets_page(request: Request):
    """Assets list page."""
    return templates.TemplateResponse(
        "pages/assets/list.html",
        {"request": request, "title": "Assets"},
    )


@app.get("/assets/{asset_id}", response_class=HTMLResponse)
async def asset_detail_page(request: Request, asset_id: int):
    """Asset detail page."""
    return templates.TemplateResponse(
        "pages/assets/detail.html",
        {"request": request, "title": "Asset", "asset_id": asset_id},
    )


@app.get("/risikoer", response_class=HTMLResponse)
async def risks_page(request: Request):
    """Risks list page."""
    return templates.TemplateResponse(
        "pages/risks/list.html",
        {"request": request, "title": "Risikoer"},
    )


@app.get("/risikoer/{risk_id}", response_class=HTMLResponse)
async def risk_detail_page(request: Request, risk_id: int):
    """Risk detail page."""
    return templates.TemplateResponse(
        "pages/risks/detail.html",
        {"request": request, "title": "Risiko", "risk_id": risk_id},
    )


@app.get("/tiltak", response_class=HTMLResponse)
async def actions_page(request: Request):
    """Actions list page."""
    return templates.TemplateResponse(
        "pages/actions/list.html",
        {"request": request, "title": "Tiltak"},
    )


@app.get("/tiltak/{action_id}", response_class=HTMLResponse)
async def action_detail_page(request: Request, action_id: int):
    """Action detail page."""
    return templates.TemplateResponse(
        "pages/actions/detail.html",
        {"request": request, "title": "Tiltak", "action_id": action_id},
    )


@app.get("/rapporter", response_class=HTMLResponse)
async def reports_page(request: Request):
    """Reports page."""
    return templates.TemplateResponse(
        "pages/reports.html",
        {"request": request, "title": "Rapporter"},
    )


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": settings.app_version}
