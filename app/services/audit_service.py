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

    async def log_export(
        self,
        entity_type: str,
        user: User,
        export_format: str = "pdf",
        **kwargs: Any,
    ) -> AuditLog:
        """Log an export action."""
        return await self.log(
            action=AuditAction.EXPORT,
            entity_type=entity_type,
            user=user,
            description=f"Eksporterte {entity_type} som {export_format}",
            **kwargs,
        )

    async def log_approve(
        self,
        entity_type: str,
        entity_id: int,
        user: User,
        rationale: str | None = None,
        **kwargs: Any,
    ) -> AuditLog:
        """Log an approval action (e.g., risk acceptance)."""
        return await self.log(
            action=AuditAction.APPROVE,
            entity_type=entity_type,
            entity_id=entity_id,
            user=user,
            new_values={"rationale": rationale} if rationale else None,
            description=f"Godkjente {entity_type} #{entity_id}",
            **kwargs,
        )

    async def get_entity_history(
        self,
        entity_type: str,
        entity_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AuditLog]:
        """
        Get audit history for a specific entity.

        Args:
            entity_type: Name of the entity (e.g., "risk", "asset")
            entity_id: ID of the entity
            limit: Maximum number of entries to return
            offset: Number of entries to skip

        Returns:
            List of AuditLog entries ordered by timestamp descending
        """
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        result = await self.db.execute(
            select(AuditLog)
            .options(selectinload(AuditLog.user))
            .where(
                AuditLog.entity_type == entity_type,
                AuditLog.entity_id == entity_id,
            )
            .order_by(AuditLog.timestamp.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_user_activity(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AuditLog]:
        """
        Get audit history for a specific user.

        Args:
            user_id: ID of the user
            limit: Maximum number of entries to return
            offset: Number of entries to skip

        Returns:
            List of AuditLog entries ordered by timestamp descending
        """
        from sqlalchemy import select

        result = await self.db.execute(
            select(AuditLog)
            .where(AuditLog.user_id == user_id)
            .order_by(AuditLog.timestamp.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_recent_activity(
        self,
        limit: int = 100,
        offset: int = 0,
        action_filter: AuditAction | None = None,
        entity_type_filter: str | None = None,
    ) -> list[AuditLog]:
        """
        Get recent audit activity.

        Args:
            limit: Maximum number of entries to return
            offset: Number of entries to skip
            action_filter: Optional filter by action type
            entity_type_filter: Optional filter by entity type

        Returns:
            List of AuditLog entries ordered by timestamp descending
        """
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        query = select(AuditLog).options(selectinload(AuditLog.user))

        if action_filter:
            query = query.where(AuditLog.action == action_filter)
        if entity_type_filter:
            query = query.where(AuditLog.entity_type == entity_type_filter)

        result = await self.db.execute(
            query.order_by(AuditLog.timestamp.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())
