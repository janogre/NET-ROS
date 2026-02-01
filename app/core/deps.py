"""
FastAPI dependencies for authentication and authorization.
"""

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.database import get_db
from app.models.user import User, UserRole


async def get_current_user(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    Hent innlogget bruker fra session/token.
    Brukes som dependency i endpoints som krever autentisering.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Ugyldig eller manglende pålogging",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Prøv først å hente token fra cookie (session-basert auth)
    token = request.cookies.get("access_token")

    # Fallback til Authorization header
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    if not token:
        raise credentials_exception

    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    user_id: int | None = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    # Hent bruker fra database
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Verifiser at brukeren er aktiv."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Brukeren er deaktivert",
        )
    return current_user


def require_role(*roles: UserRole) -> Callable:
    """
    Dependency factory for å kreve bestemte roller.

    Bruk:
        @router.get("/admin", dependencies=[Depends(require_role(UserRole.ADMIN))])
    """

    async def role_checker(
        current_user: Annotated[User, Depends(get_current_active_user)],
    ) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Utilstrekkelige rettigheter",
            )
        return current_user

    return role_checker


# Convenience dependencies for common role checks
RequireAdmin = Depends(require_role(UserRole.ADMIN))
RequireRisikoansvarlig = Depends(
    require_role(UserRole.ADMIN, UserRole.RISIKOANSVARLIG)
)
RequireBruker = Depends(
    require_role(UserRole.ADMIN, UserRole.RISIKOANSVARLIG, UserRole.BRUKER)
)
