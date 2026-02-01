"""
Report service for generating PDF reports.
"""

from datetime import date, datetime
from io import BytesIO

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.risk import Risk
from app.models.asset import Asset
from app.models.action import Action, ActionStatus
from app.models.project import Project
from app.services.risk_service import RiskService


class ReportService:
    """Service for generating reports."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.risk_service = RiskService(db)

    async def generate_risk_register_html(
        self,
        project_id: int | None = None,
    ) -> str:
        """Generate HTML for risk register report."""
        # Fetch risks
        query = select(Risk).options(
            selectinload(Risk.owner),
            selectinload(Risk.asset_associations).selectinload(
                Risk.asset_associations.property.mapper.class_.asset
            ),
        )
        if project_id:
            query = query.where(Risk.project_id == project_id)

        result = await self.db.execute(query)
        risks = result.scalars().all()

        # Fetch project if specified
        project = None
        if project_id:
            proj_result = await self.db.execute(
                select(Project).where(Project.id == project_id)
            )
            project = proj_result.scalar_one_or_none()

        # Build HTML
        html = f"""
<!DOCTYPE html>
<html lang="no">
<head>
    <meta charset="UTF-8">
    <title>Risikoregister - {settings.company_name}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 40px;
            color: #333;
        }}
        h1 {{
            color: #1a365d;
            border-bottom: 2px solid #2b6cb0;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #2d3748;
            margin-top: 30px;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 20px;
        }}
        .meta {{
            color: #718096;
            font-size: 0.9em;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            border: 1px solid #e2e8f0;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #2b6cb0;
            color: white;
        }}
        tr:nth-child(even) {{
            background-color: #f7fafc;
        }}
        .risk-green {{ background-color: #c6f6d5; }}
        .risk-yellow {{ background-color: #fefcbf; }}
        .risk-orange {{ background-color: #fbd38d; }}
        .risk-red {{ background-color: #feb2b2; }}
        .score {{
            font-weight: bold;
            text-align: center;
            padding: 5px 10px;
            border-radius: 4px;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e2e8f0;
            font-size: 0.8em;
            color: #718096;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h1>Risikoregister</h1>
            <p class="meta">{settings.company_name}</p>
        </div>
        <div class="meta">
            <p>Generert: {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
            {f'<p>Prosjekt: {project.name}</p>' if project else ''}
        </div>
    </div>

    <table>
        <thead>
            <tr>
                <th>#</th>
                <th>Risiko</th>
                <th>Type</th>
                <th>S</th>
                <th>K</th>
                <th>Score</th>
                <th>Status</th>
                <th>Ansvarlig</th>
            </tr>
        </thead>
        <tbody>
"""
        for i, risk in enumerate(risks, 1):
            color_class = f"risk-{risk.risk_color}"
            owner_name = risk.owner.full_name if risk.owner else "-"
            html += f"""
            <tr>
                <td>{i}</td>
                <td>{risk.title}</td>
                <td>{risk.risk_type.value}</td>
                <td>{risk.likelihood}</td>
                <td>{risk.consequence}</td>
                <td><span class="score {color_class}">{risk.risk_score}</span></td>
                <td>{risk.status.value}</td>
                <td>{owner_name}</td>
            </tr>
"""

        html += f"""
        </tbody>
    </table>

    <div class="footer">
        <p>Dette dokumentet er generert av NetROS - ROS-analyseverktøy for {settings.company_name}</p>
        <p>Dokumentet inneholder {len(risks)} risikoer.</p>
    </div>
</body>
</html>
"""
        return html

    async def generate_nkom_summary_html(
        self,
        project_id: int | None = None,
    ) -> str:
        """Generate Nkom-formatted summary report."""
        # Get risk matrix
        current_matrix = await self.risk_service.get_risk_matrix(project_id)
        target_matrix = await self.risk_service.get_target_risk_matrix(project_id)
        distribution = await self.risk_service.get_risk_distribution(project_id)

        # Get actions summary
        action_query = select(Action)
        action_result = await self.db.execute(action_query)
        actions = action_result.scalars().all()

        completed = sum(1 for a in actions if a.status == ActionStatus.FULLFORT)
        overdue = sum(1 for a in actions if a.is_overdue)

        html = f"""
<!DOCTYPE html>
<html lang="no">
<head>
    <meta charset="UTF-8">
    <title>ROS-sammendrag for Nkom - {settings.company_name}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 40px;
            color: #333;
        }}
        h1 {{
            color: #1a365d;
            border-bottom: 2px solid #2b6cb0;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #2d3748;
            margin-top: 30px;
        }}
        .summary-box {{
            background: #f7fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }}
        .stat {{
            display: inline-block;
            margin: 10px 20px 10px 0;
        }}
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #2b6cb0;
        }}
        .stat-label {{
            color: #718096;
            font-size: 0.9em;
        }}
        .matrix {{
            display: inline-block;
            border-collapse: collapse;
            margin: 10px;
        }}
        .matrix td {{
            width: 40px;
            height: 40px;
            text-align: center;
            border: 1px solid #e2e8f0;
            font-weight: bold;
        }}
        .cell-green {{ background-color: #c6f6d5; }}
        .cell-yellow {{ background-color: #fefcbf; }}
        .cell-orange {{ background-color: #fbd38d; }}
        .cell-red {{ background-color: #feb2b2; }}
        .compliance {{
            margin-top: 30px;
        }}
        .compliance-item {{
            padding: 10px;
            margin: 5px 0;
            background: #f0fff4;
            border-left: 4px solid #48bb78;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e2e8f0;
            font-size: 0.8em;
            color: #718096;
        }}
    </style>
</head>
<body>
    <h1>ROS-analyse sammendrag</h1>
    <p><strong>{settings.company_name}</strong> - Org.nr: {settings.company_org_nr}</p>
    <p>Rapport generert: {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>

    <div class="summary-box">
        <h2>Risikooversikt</h2>
        <div class="stat">
            <div class="stat-value">{current_matrix.total_risks}</div>
            <div class="stat-label">Totalt antall risikoer</div>
        </div>
        <div class="stat">
            <div class="stat-value" style="color: #e53e3e;">{distribution['red']}</div>
            <div class="stat-label">Høy risiko (17-25)</div>
        </div>
        <div class="stat">
            <div class="stat-value" style="color: #dd6b20;">{distribution['orange']}</div>
            <div class="stat-label">Middels risiko (10-16)</div>
        </div>
        <div class="stat">
            <div class="stat-value" style="color: #d69e2e;">{distribution['yellow']}</div>
            <div class="stat-label">Lav risiko (5-9)</div>
        </div>
        <div class="stat">
            <div class="stat-value" style="color: #38a169;">{distribution['green']}</div>
            <div class="stat-label">Akseptabel (1-4)</div>
        </div>
    </div>

    <div class="summary-box">
        <h2>Tiltaksstatus</h2>
        <div class="stat">
            <div class="stat-value">{len(actions)}</div>
            <div class="stat-label">Totalt antall tiltak</div>
        </div>
        <div class="stat">
            <div class="stat-value" style="color: #38a169;">{completed}</div>
            <div class="stat-label">Fullført</div>
        </div>
        <div class="stat">
            <div class="stat-value" style="color: #e53e3e;">{overdue}</div>
            <div class="stat-label">Forfalt</div>
        </div>
    </div>

    <div class="compliance">
        <h2>Regulatorisk samsvar</h2>
        <div class="compliance-item">
            <strong>Ekomforskriften § 2-5:</strong> Dokumenterte ROS-analyser er gjennomført
        </div>
        <div class="compliance-item">
            <strong>NSMs Grunnprinsipper:</strong> Risikoer er kartlagt mot relevante prinsipper
        </div>
    </div>

    <div class="footer">
        <p>Dette dokumentet er utarbeidet i henhold til krav fra Nasjonal kommunikasjonsmyndighet (Nkom).</p>
        <p>Generert av NetROS - ROS-analyseverktøy</p>
    </div>
</body>
</html>
"""
        return html

    async def generate_pdf(self, html_content: str) -> bytes:
        """Convert HTML to PDF using WeasyPrint."""
        try:
            from weasyprint import HTML

            pdf_buffer = BytesIO()
            HTML(string=html_content).write_pdf(pdf_buffer)
            return pdf_buffer.getvalue()
        except ImportError:
            raise RuntimeError(
                "WeasyPrint er ikke installert. Kjør: pip install weasyprint"
            )

    async def generate_risk_register_pdf(
        self,
        project_id: int | None = None,
    ) -> bytes:
        """Generate PDF risk register."""
        html = await self.generate_risk_register_html(project_id)
        return await self.generate_pdf(html)

    async def generate_nkom_summary_pdf(
        self,
        project_id: int | None = None,
    ) -> bytes:
        """Generate PDF Nkom summary."""
        html = await self.generate_nkom_summary_html(project_id)
        return await self.generate_pdf(html)
