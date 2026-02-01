"""
Pydantic schemas for Dashboard.
"""

from pydantic import BaseModel


class RiskDistribution(BaseModel):
    """Fordeling av risikoer per nivå."""

    green: int = 0  # Akseptabel (1-4)
    yellow: int = 0  # Lav (5-9)
    orange: int = 0  # Middels (10-16)
    red: int = 0  # Høy (17-25)
    total: int = 0


class ActionProgress(BaseModel):
    """Fremdrift på tiltak."""

    planlagt: int = 0
    pagaende: int = 0
    fullfort: int = 0
    forfalt: int = 0
    total: int = 0


class DashboardSummary(BaseModel):
    """Sammendrag for dashboard."""

    total_assets: int = 0
    total_risks: int = 0
    total_actions: int = 0
    overdue_actions: int = 0
    upcoming_reviews: int = 0
    risk_distribution: RiskDistribution = RiskDistribution()
    action_progress: ActionProgress = ActionProgress()
    recent_risks: list = []
    critical_risks: list = []
