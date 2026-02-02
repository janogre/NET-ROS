#!/usr/bin/env python
"""
Seed NSM Grunnprinsipper for IKT-sikkerhet.
Kjør: python scripts/init_nsm_principles.py
"""

import asyncio
import sys
from datetime import date
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.database import async_session_maker, init_db
from app.models.nsm import NSMPrinciple, NSMCategory

# NSM versjon
NSM_VERSION = "2.0"
NSM_EFFECTIVE_DATE = date(2023, 1, 1)  # NSM Grunnprinsipper 2.0 ble lansert 2023

# NSM Grunnprinsipper data
NSM_PRINCIPLES = [
    # Kategori 1: Identifisere
    {"code": "1.1", "category": NSMCategory.IDENTIFISERE, "title": "Kartlegg virksomhetens verdier", "sort_order": 1},
    {"code": "1.2", "category": NSMCategory.IDENTIFISERE, "title": "Kartlegg verdikjeder og avhengigheter", "sort_order": 2},
    {"code": "1.3", "category": NSMCategory.IDENTIFISERE, "title": "Kartlegg enheter og programvare", "sort_order": 3},
    {"code": "1.4", "category": NSMCategory.IDENTIFISERE, "title": "Kartlegg brukere og tilganger", "sort_order": 4},
    {"code": "1.5", "category": NSMCategory.IDENTIFISERE, "title": "Kartlegg sårbarheter", "sort_order": 5},
    {"code": "1.6", "category": NSMCategory.IDENTIFISERE, "title": "Vurder risiko", "sort_order": 6},

    # Kategori 2: Beskytte
    {"code": "2.1", "category": NSMCategory.BESKYTTE, "title": "Ivareta sikkerhet i anskaffelser", "sort_order": 7},
    {"code": "2.2", "category": NSMCategory.BESKYTTE, "title": "Etabler en sikker IKT-arkitektur", "sort_order": 8},
    {"code": "2.3", "category": NSMCategory.BESKYTTE, "title": "Ivareta en sikker konfigurasjon", "sort_order": 9},
    {"code": "2.4", "category": NSMCategory.BESKYTTE, "title": "Beskytt virksomhetens nettverk", "sort_order": 10},
    {"code": "2.5", "category": NSMCategory.BESKYTTE, "title": "Kontroller dataflyt", "sort_order": 11},
    {"code": "2.6", "category": NSMCategory.BESKYTTE, "title": "Ha kontroll på identiteter og tilganger", "sort_order": 12},
    {"code": "2.7", "category": NSMCategory.BESKYTTE, "title": "Beskytt data i ro og i transitt", "sort_order": 13},
    {"code": "2.8", "category": NSMCategory.BESKYTTE, "title": "Beskytt e-post og nettleser", "sort_order": 14},
    {"code": "2.9", "category": NSMCategory.BESKYTTE, "title": "Etabler evne til gjenoppretting av data", "sort_order": 15},
    {"code": "2.10", "category": NSMCategory.BESKYTTE, "title": "Integrer sikkerhet i prosess for endringshåndtering", "sort_order": 16},

    # Kategori 3: Oppdage
    {"code": "3.1", "category": NSMCategory.OPPDAGE, "title": "Oppdag og fjern kjente sårbarheter og trusler", "sort_order": 17},
    {"code": "3.2", "category": NSMCategory.OPPDAGE, "title": "Etabler sikkerhetsovervåking", "sort_order": 18},
    {"code": "3.3", "category": NSMCategory.OPPDAGE, "title": "Analyser data fra sikkerhetsovervåking", "sort_order": 19},
    {"code": "3.4", "category": NSMCategory.OPPDAGE, "title": "Gjennomfør inntrengningstester", "sort_order": 20},

    # Kategori 4: Håndtere og gjenopprette
    {"code": "4.1", "category": NSMCategory.HANDTERE, "title": "Forbered virksomheten på å håndtere hendelser", "sort_order": 21},
    {"code": "4.2", "category": NSMCategory.HANDTERE, "title": "Vurder exceptions", "sort_order": 22},
    {"code": "4.3", "category": NSMCategory.HANDTERE, "title": "Håndter hendelser effektivt", "sort_order": 23},
    {"code": "4.4", "category": NSMCategory.HANDTERE, "title": "Lær av sikkerhetshendelser", "sort_order": 24},
]


async def seed_nsm_principles():
    """Seed NSM principles to database."""
    # Initialize database
    await init_db()

    async with async_session_maker() as session:
        # Check if already seeded
        result = await session.execute(select(NSMPrinciple).limit(1))
        if result.scalar_one_or_none():
            print("NSM-prinsipper er allerede lagt inn i databasen.")
            return

        # Insert principles
        for principle_data in NSM_PRINCIPLES:
            principle = NSMPrinciple(
                code=principle_data["code"],
                category=principle_data["category"],
                title=principle_data["title"],
                description=principle_data.get("description"),
                sort_order=principle_data["sort_order"],
                version=NSM_VERSION,
                effective_date=NSM_EFFECTIVE_DATE,
            )
            session.add(principle)

        await session.commit()
        print(f"La inn {len(NSM_PRINCIPLES)} NSM-prinsipper i databasen.")


if __name__ == "__main__":
    asyncio.run(seed_nsm_principles())
