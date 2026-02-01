"""
Risk service for business logic related to risks and risk matrix.
"""

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.risk import Risk, AssetRisk, NSMMapping
from app.models.asset import Asset
from app.models.nsm import NSMPrinciple
from app.schemas.risk import RiskCreate, RiskUpdate, RiskMatrix, RiskMatrixCell, RiskSummary


class RiskService:
    """Service for risk-related operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def get_risk_color(score: int) -> str:
        """Get CSS color class for risk score."""
        if score <= 4:
            return "green"
        elif score <= 9:
            return "yellow"
        elif score <= 16:
            return "orange"
        else:
            return "red"

    @staticmethod
    def get_risk_level(score: int) -> str:
        """Get Norwegian risk level label."""
        if score <= 4:
            return "Akseptabel"
        elif score <= 9:
            return "Lav"
        elif score <= 16:
            return "Middels"
        else:
            return "Høy"

    async def get_risk_matrix(self, project_id: int | None = None) -> RiskMatrix:
        """
        Generate a 5x5 risk matrix with risks placed in cells.

        Args:
            project_id: Optional filter by project

        Returns:
            RiskMatrix with cells containing risk data
        """
        # Build query with project relationship for tooltip
        query = select(Risk).options(selectinload(Risk.project))
        if project_id:
            query = query.where(Risk.project_id == project_id)

        result = await self.db.execute(query)
        risks = result.scalars().all()

        # Initialize 5x5 matrix (likelihood rows, consequence columns)
        # Row 0 = likelihood 5 (top), Row 4 = likelihood 1 (bottom)
        # Col 0 = consequence 1 (left), Col 4 = consequence 5 (right)
        cells: list[list[RiskMatrixCell]] = []

        for likelihood in range(5, 0, -1):  # 5, 4, 3, 2, 1
            row: list[RiskMatrixCell] = []
            for consequence in range(1, 6):  # 1, 2, 3, 4, 5
                score = likelihood * consequence
                cell = RiskMatrixCell(
                    likelihood=likelihood,
                    consequence=consequence,
                    score=score,
                    color=self.get_risk_color(score),
                    risk_ids=[],
                    risk_count=0,
                    risks=[],
                )
                row.append(cell)
            cells.append(row)

        # Place risks in matrix
        total_risks = 0
        for risk in risks:
            total_risks += 1
            # Calculate row and column indices
            row_idx = 5 - risk.likelihood  # 5 -> 0, 1 -> 4
            col_idx = risk.consequence - 1  # 1 -> 0, 5 -> 4
            cells[row_idx][col_idx].risk_ids.append(risk.id)
            cells[row_idx][col_idx].risk_count += 1
            cells[row_idx][col_idx].risks.append(
                RiskSummary(
                    id=risk.id,
                    title=risk.title,
                    project_name=risk.project.name if risk.project else None,
                )
            )

        return RiskMatrix(cells=cells, total_risks=total_risks)

    async def get_target_risk_matrix(
        self, project_id: int | None = None
    ) -> RiskMatrix:
        """
        Generate target (after measures) risk matrix.
        Uses target_likelihood and target_consequence if set.
        """
        query = select(Risk).options(selectinload(Risk.project))
        if project_id:
            query = query.where(Risk.project_id == project_id)

        result = await self.db.execute(query)
        risks = result.scalars().all()

        cells: list[list[RiskMatrixCell]] = []

        for likelihood in range(5, 0, -1):
            row: list[RiskMatrixCell] = []
            for consequence in range(1, 6):
                score = likelihood * consequence
                cell = RiskMatrixCell(
                    likelihood=likelihood,
                    consequence=consequence,
                    score=score,
                    color=self.get_risk_color(score),
                    risk_ids=[],
                    risk_count=0,
                    risks=[],
                )
                row.append(cell)
            cells.append(row)

        total_risks = 0
        for risk in risks:
            # Use target values if set, otherwise current values
            likelihood = risk.target_likelihood or risk.likelihood
            consequence = risk.target_consequence or risk.consequence

            total_risks += 1
            row_idx = 5 - likelihood
            col_idx = consequence - 1
            cells[row_idx][col_idx].risk_ids.append(risk.id)
            cells[row_idx][col_idx].risk_count += 1
            cells[row_idx][col_idx].risks.append(
                RiskSummary(
                    id=risk.id,
                    title=risk.title,
                    project_name=risk.project.name if risk.project else None,
                )
            )

        return RiskMatrix(cells=cells, total_risks=total_risks)

    async def create_risk(self, risk_data: RiskCreate) -> Risk:
        """Create a new risk with asset and NSM associations."""
        # Create risk
        risk = Risk(
            title=risk_data.title,
            description=risk_data.description,
            risk_type=risk_data.risk_type,
            project_id=risk_data.project_id,
            likelihood=risk_data.likelihood,
            consequence=risk_data.consequence,
            target_likelihood=risk_data.target_likelihood,
            target_consequence=risk_data.target_consequence,
            status=risk_data.status,
            owner_id=risk_data.owner_id,
            owner_department_id=risk_data.owner_department_id,
            vulnerability_description=risk_data.vulnerability_description,
            threat_description=risk_data.threat_description,
            existing_controls=risk_data.existing_controls,
            proposed_measures=risk_data.proposed_measures,
            next_review_date=risk_data.next_review_date,
        )
        self.db.add(risk)
        await self.db.flush()

        # Add asset associations
        for asset_id in risk_data.asset_ids:
            asset_risk = AssetRisk(asset_id=asset_id, risk_id=risk.id)
            self.db.add(asset_risk)

        # Add NSM mappings
        for nsm_id in risk_data.nsm_principle_ids:
            nsm_mapping = NSMMapping(nsm_principle_id=nsm_id, risk_id=risk.id)
            self.db.add(nsm_mapping)

        await self.db.commit()
        await self.db.refresh(risk)
        return risk

    async def update_risk(self, risk_id: int, risk_data: RiskUpdate) -> Risk | None:
        """Update an existing risk."""
        result = await self.db.execute(select(Risk).where(Risk.id == risk_id))
        risk = result.scalar_one_or_none()

        if not risk:
            return None

        # Update fields
        update_data = risk_data.model_dump(exclude_unset=True)
        asset_ids = update_data.pop("asset_ids", None)
        nsm_principle_ids = update_data.pop("nsm_principle_ids", None)

        for field, value in update_data.items():
            setattr(risk, field, value)

        # Update asset associations if provided
        if asset_ids is not None:
            # Remove existing
            await self.db.execute(
                AssetRisk.__table__.delete().where(AssetRisk.risk_id == risk_id)
            )
            # Add new
            for asset_id in asset_ids:
                asset_risk = AssetRisk(asset_id=asset_id, risk_id=risk.id)
                self.db.add(asset_risk)

        # Update NSM mappings if provided
        if nsm_principle_ids is not None:
            await self.db.execute(
                NSMMapping.__table__.delete().where(NSMMapping.risk_id == risk_id)
            )
            for nsm_id in nsm_principle_ids:
                nsm_mapping = NSMMapping(nsm_principle_id=nsm_id, risk_id=risk.id)
                self.db.add(nsm_mapping)

        await self.db.commit()
        await self.db.refresh(risk)
        return risk

    async def get_risk_distribution(
        self, project_id: int | None = None
    ) -> dict[str, int]:
        """Get risk count by level."""
        query = select(Risk)
        if project_id:
            query = query.where(Risk.project_id == project_id)

        result = await self.db.execute(query)
        risks = result.scalars().all()

        distribution = {"green": 0, "yellow": 0, "orange": 0, "red": 0}
        for risk in risks:
            color = self.get_risk_color(risk.risk_score)
            distribution[color] += 1

        return distribution

    async def get_nsm_coverage(self) -> dict:
        """Get NSM principle coverage statistics."""
        # Get all principles
        principles_result = await self.db.execute(select(NSMPrinciple))
        principles = principles_result.scalars().all()

        # Get mapped principles
        mappings_result = await self.db.execute(
            select(NSMMapping.nsm_principle_id).distinct()
        )
        mapped_ids = {row[0] for row in mappings_result.all()}

        coverage = {
            "total_principles": len(principles),
            "mapped_principles": len(mapped_ids),
            "coverage_percent": (
                round(len(mapped_ids) / len(principles) * 100, 1)
                if principles
                else 0
            ),
            "unmapped": [
                {"id": p.id, "code": p.code, "title": p.title}
                for p in principles
                if p.id not in mapped_ids
            ],
        }
        return coverage
