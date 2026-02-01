#!/usr/bin/env python
"""
Opprett admin-bruker for NetROS.
Kjør: python scripts/create_admin.py
"""

import asyncio
import getpass
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.database import async_session_maker, init_db
from app.models.user import User, UserRole
from app.core.security import get_password_hash


async def create_admin():
    """Opprett admin-bruker interaktivt."""
    # Initialize database
    await init_db()

    print("\n=== NetROS Admin Bruker Oppsett ===\n")

    # Get user input
    username = input("Brukernavn [admin]: ").strip() or "admin"
    email = input("E-post [admin@neas.no]: ").strip() or "admin@neas.no"
    full_name = input("Fullt navn [Administrator]: ").strip() or "Administrator"
    password = getpass.getpass("Passord (min 8 tegn): ")

    if len(password) < 8:
        print("Feil: Passord må være minst 8 tegn.")
        return

    password_confirm = getpass.getpass("Bekreft passord: ")
    if password != password_confirm:
        print("Feil: Passordene stemmer ikke overens.")
        return

    async with async_session_maker() as session:
        # Check if username exists
        result = await session.execute(
            select(User).where(User.username == username)
        )
        if result.scalar_one_or_none():
            print(f"Feil: Brukernavn '{username}' finnes allerede.")
            return

        # Check if email exists
        result = await session.execute(
            select(User).where(User.email == email)
        )
        if result.scalar_one_or_none():
            print(f"Feil: E-post '{email}' er allerede i bruk.")
            return

        # Create admin user
        admin = User(
            username=username,
            email=email,
            full_name=full_name,
            hashed_password=get_password_hash(password),
            role=UserRole.ADMIN,
            is_active=True,
        )
        session.add(admin)
        await session.commit()

        print(f"\nAdmin-bruker opprettet!")
        print(f"  Brukernavn: {username}")
        print(f"  E-post: {email}")
        print(f"  Rolle: {UserRole.ADMIN.value}")
        print(f"\nDu kan nå logge inn på http://localhost:8000/login")


if __name__ == "__main__":
    asyncio.run(create_admin())
