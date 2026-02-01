"""
Audit service for logging changes.
"""

import json
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog, AuditAction
from app.models.user import User


class AuditService:
    """Service for audit logging."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(
        self,
        action: AuditAction,
        entity_type: str,
        entity_id: int | None = None,
        user: User | None = None,
        old_values: dict[str, Any] | None = None,
        new_values: dict[str, Any] | None = None,
        description: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        """
        Log an action to the audit trail.

        Args:
            action: Type of action (create, update, delete, etc.)
            entity_type: Name of the entity being modified
            entity_id: ID of the entity
            user: User performing the action
            old_values: Previous values (for updates)
            new_values: New values (for creates/updates)
            description: Human-readable description
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Created AuditLog entry
        """
        log_entry = AuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user.id if user else None,
            old_values=json.dumps(old_values) if old_values else None,
            new_values=json.dumps(new_values) if new_values else None,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.add(log_entry)
        await self.db.flush()

        return log_entry

    async def log_create(
        self,
        entity_type: str,
        entity_id: int,
        user: User | None = None,
        values: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> AuditLog:
        """Log a create action."""
        return await self.log(
            action=AuditAction.CREATE,
            entity_type=entity_type,
            entity_id=entity_id,
            user=user,
            new_values=values,
            description=f"Opprettet {entity_type} #{entity_id}",
            **kwargs,
        )

    async def log_update(
        self,
        entity_type: str,
        entity_id: int,
        user: User | None = None,
        old_values: dict[str, Any] | None = None,
        new_values: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> AuditLog:
        """Log an update action."""
        return await self.log(
            action=AuditAction.UPDATE,
            entity_type=entity_type,
            entity_id=entity_id,
            user=user,
            old_values=old_values,
            new_values=new_values,
            description=f"Oppdaterte {entity_type} #{entity_id}",
            **kwargs,
        )

    async def log_delete(
        self,
        entity_type: str,
        entity_id: int,
        user: User | None = None,
        values: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> AuditLog:
        """Log a delete action."""
        return await self.log(
            action=AuditAction.DELETE,
            entity_type=entity_type,
            entity_id=entity_id,
            user=user,
            old_values=values,
            description=f"Slettet {entity_type} #{entity_id}",
            **kwargs,
        )

    async def log_login(
        self,
        user: User,
        **kwargs: Any,
    ) -> AuditLog:
        """Log a login action."""
        return await self.log(
            action=AuditAction.LOGIN,
            entity_type="user",
            entity_id=user.id,
            user=user,
            description=f"Bruker {user.username} logget inn",
            **kwargs,
        )

    async def log_logout(
        self,
        user: User,
        **kwargs: Any,
    ) -> AuditLog:
        """Log a logout action."""
        return await self.log(
            action=AuditAction.LOGOUT,
            entity_type="user",
            entity_id=user.id,
            user=user,
            description=f"Bruker {user.username} logget ut",
            **kwargs,
        )
