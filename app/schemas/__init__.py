"""
Pydantic schemas for NetROS.
"""

from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserLogin,
    Token,
    TokenData,
)
from app.schemas.department import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
)
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
)
from app.schemas.asset import (
    AssetCreate,
    AssetUpdate,
    AssetResponse,
)
from app.schemas.supplier import (
    SupplierCreate,
    SupplierUpdate,
    SupplierResponse,
)
from app.schemas.risk import (
    RiskCreate,
    RiskUpdate,
    RiskResponse,
    RiskMatrixCell,
    RiskMatrix,
)
from app.schemas.action import (
    ActionCreate,
    ActionUpdate,
    ActionResponse,
)
from app.schemas.review import (
    ReviewCreate,
    ReviewUpdate,
    ReviewResponse,
)
from app.schemas.information_asset import (
    InformationAssetCreate,
    InformationAssetUpdate,
    InformationAssetResponse,
)
from app.schemas.document import (
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
    DocumentLinkCreate,
    DocumentLinkResponse,
    DocumentWithLinksResponse,
)
from app.schemas.ekomforskriften import (
    EkomPrincipleCreate,
    EkomPrincipleUpdate,
    EkomPrincipleResponse,
    EkomMappingCreate,
    EkomMappingUpdate,
    EkomMappingResponse,
    EkomComplianceSummary,
)
from app.schemas.dashboard import (
    DashboardSummary,
    RiskDistribution,
    ActionProgress,
)

__all__ = [
    # User
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserLogin",
    "Token",
    "TokenData",
    # Department
    "DepartmentCreate",
    "DepartmentUpdate",
    "DepartmentResponse",
    # Project
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectResponse",
    # Asset
    "AssetCreate",
    "AssetUpdate",
    "AssetResponse",
    # Supplier
    "SupplierCreate",
    "SupplierUpdate",
    "SupplierResponse",
    # Risk
    "RiskCreate",
    "RiskUpdate",
    "RiskResponse",
    "RiskMatrixCell",
    "RiskMatrix",
    # Action
    "ActionCreate",
    "ActionUpdate",
    "ActionResponse",
    # Review
    "ReviewCreate",
    "ReviewUpdate",
    "ReviewResponse",
    # InformationAsset
    "InformationAssetCreate",
    "InformationAssetUpdate",
    "InformationAssetResponse",
    # Document
    "DocumentCreate",
    "DocumentUpdate",
    "DocumentResponse",
    "DocumentLinkCreate",
    "DocumentLinkResponse",
    "DocumentWithLinksResponse",
    # Ekomforskriften
    "EkomPrincipleCreate",
    "EkomPrincipleUpdate",
    "EkomPrincipleResponse",
    "EkomMappingCreate",
    "EkomMappingUpdate",
    "EkomMappingResponse",
    "EkomComplianceSummary",
    # Dashboard
    "DashboardSummary",
    "RiskDistribution",
    "ActionProgress",
]
