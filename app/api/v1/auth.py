"""
Authentication endpoints for NetROS.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_password, create_access_token
from app.core.deps import get_current_active_user
from app.database import get_db
from app.models.user import User
from app.schemas.user import Token, UserResponse
from app.services.audit_service import AuditService

router = APIRouter()


@router.post("/login", response_model=Token)
async def login(
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
) -> Token:
    """
    Logg inn med brukernavn og passord.
    Setter en session-cookie med JWT token.
    """
    # Find user
    result = await db.execute(
        select(User).where(User.username == username)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Feil brukernavn eller passord",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Brukeren er deaktivert",
        )

    # Create token
    access_token = create_access_token(data={"sub": str(user.id)})

    # Set cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=60 * 60 * 8,  # 8 hours
    )

    # Log login
    audit_service = AuditService(db)
    await audit_service.log_login(user)
    await db.commit()

    return Token(access_token=access_token)


@router.post("/logout")
async def logout(
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """Logg ut og fjern session-cookie."""
    # Clear cookie
    response.delete_cookie(key="access_token")

    # Log logout
    audit_service = AuditService(db)
    await audit_service.log_logout(current_user)
    await db.commit()

    return {"message": "Logget ut"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    """Hent informasjon om innlogget bruker."""
    return current_user
