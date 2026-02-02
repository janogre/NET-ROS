#!/usr/bin/env python
"""
Initialize Ekomforskriften principles in the database.
Forskrift om elektronisk kommunikasjonsnett og elektronisk kommunikasjonstjeneste.
"""

import asyncio
import sys
from datetime import date
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.database import async_session
from app.models.ekomforskriften import EkomPrinciple, EkomCategory, EkomParagraph

# Ekomforskriften versjon
EKOM_VERSION = "2024"
EKOM_EFFECTIVE_DATE = date(2024, 1, 1)


EKOM_PRINCIPLES = [
    # Kapittel 2: Sikkerhet og beredskap
    {
        "code": "2-1",
        "paragraph": EkomParagraph.PARA_2_1,
        "category": EkomCategory.SIKKERHET,
        "title": "Krav om sikkerhet",
        "description": "Tilbyder skal sørge for forsvarlig sikkerhet for brukerne og nett og tjenester mot brudd på konfidensialitet, integritet og tilgjengelighet.",
        "legal_text": "Tilbyder skal sørge for forsvarlig sikkerhet i nett og tjenester. Tiltakene skal stå i forhold til risikoen.",
        "sort_order": 10,
    },
    {
        "code": "2-2",
        "paragraph": EkomParagraph.PARA_2_2,
        "category": EkomCategory.SIKKERHET,
        "title": "Sikkerhetstiltak",
        "description": "Tilbyder skal iverksette tekniske og organisatoriske tiltak for å sikre nett og tjenester.",
        "legal_text": "Tilbyder skal treffe egnede tekniske og organisatoriske tiltak for å sikre nett og tjenester.",
        "sort_order": 20,
    },
    {
        "code": "2-3",
        "paragraph": EkomParagraph.PARA_2_3,
        "category": EkomCategory.SIKKERHET,
        "title": "Sikkerhetsgodkjenning",
        "description": "Myndigheten kan kreve at tilbyder dokumenterer sikkerhetstiltak og rutiner.",
        "legal_text": "Myndigheten kan kreve at tilbyder dokumenterer sikkerhetstiltak og rutiner.",
        "sort_order": 30,
    },
    {
        "code": "2-4",
        "paragraph": EkomParagraph.PARA_2_4,
        "category": EkomCategory.SIKKERHET,
        "title": "Beredskap",
        "description": "Tilbyder skal ha beredskapsplaner og -tiltak for å opprettholde nett og tjenester ved ekstraordinære situasjoner.",
        "legal_text": "Tilbyder skal utarbeide og vedlikeholde beredskapsplaner og -tiltak tilpasset virksomhetens art og omfang.",
        "sort_order": 40,
    },
    {
        "code": "2-5",
        "paragraph": EkomParagraph.PARA_2_5,
        "category": EkomCategory.KONFIDENSIALITET,
        "title": "Konfidensialitet",
        "description": "Tilbyder skal sørge for konfidensialitet for kommunikasjonsinnhold og trafikkdata.",
        "legal_text": "Tilbyder skal sørge for konfidensialitet for innholdet i elektronisk kommunikasjon og for trafikkdata.",
        "sort_order": 50,
    },
    {
        "code": "2-6",
        "paragraph": EkomParagraph.PARA_2_6,
        "category": EkomCategory.DOKUMENTASJON,
        "title": "Risiko- og sårbarhetsanalyser",
        "description": "Tilbyder skal gjennomføre risiko- og sårbarhetsanalyser og dokumentere disse.",
        "legal_text": "Tilbyder skal gjennomføre risiko- og sårbarhetsanalyser tilpasset virksomhetens art og omfang. Analysene skal dokumenteres og holdes oppdatert.",
        "sort_order": 60,
    },
    {
        "code": "2-7",
        "paragraph": EkomParagraph.PARA_2_7,
        "category": EkomCategory.VARSLING,
        "title": "Varslingsplikt",
        "description": "Tilbyder skal varsle myndigheten om sikkerhetsbrudd og integritetskrenkelser.",
        "legal_text": "Tilbyder skal uten ugrunnet opphold varsle myndigheten om brudd på sikkerheten eller integritetskrenkelser som kan ha betydelig innvirkning på driften av nett eller tjenester.",
        "sort_order": 70,
    },
    {
        "code": "2-8",
        "paragraph": EkomParagraph.PARA_2_8,
        "category": EkomCategory.DOKUMENTASJON,
        "title": "Dokumentasjonsplikt",
        "description": "Tilbyder skal dokumentere sikkerhetstiltak, rutiner og analyser.",
        "legal_text": "Tilbyder skal dokumentere sikkerhetstiltak og rutiner. Dokumentasjonen skal være tilgjengelig for myndigheten.",
        "sort_order": 80,
    },
    {
        "code": "2-9",
        "paragraph": EkomParagraph.PARA_2_9,
        "category": EkomCategory.DOKUMENTASJON,
        "title": "Tilsyn",
        "description": "Myndigheten fører tilsyn med at kravene i forskriften etterleves.",
        "legal_text": "Myndigheten fører tilsyn med at kravene i dette kapittelet etterleves.",
        "sort_order": 90,
    },
    {
        "code": "2-10",
        "paragraph": EkomParagraph.PARA_2_10,
        "category": EkomCategory.SIKKERHET,
        "title": "Pålegg",
        "description": "Myndigheten kan gi pålegg om tiltak for å sikre nett og tjenester.",
        "legal_text": "Myndigheten kan gi pålegg om tiltak for å sikre nett og tjenester.",
        "sort_order": 100,
    },
]


async def init_ekom_principles():
    """Initialize Ekomforskriften principles in database."""
    async with async_session() as session:
        for principle_data in EKOM_PRINCIPLES:
            # Check if principle already exists
            result = await session.execute(
                select(EkomPrinciple).where(EkomPrinciple.code == principle_data["code"])
            )
            existing = result.scalar_one_or_none()

            if existing:
                print(f"  Oppdaterer: § {principle_data['code']} - {principle_data['title']}")
                for key, value in principle_data.items():
                    setattr(existing, key, value)
                existing.version = EKOM_VERSION
                existing.effective_date = EKOM_EFFECTIVE_DATE
            else:
                print(f"  Oppretter: § {principle_data['code']} - {principle_data['title']}")
                principle = EkomPrinciple(
                    **principle_data,
                    version=EKOM_VERSION,
                    effective_date=EKOM_EFFECTIVE_DATE,
                )
                session.add(principle)

        await session.commit()
        print(f"\n{len(EKOM_PRINCIPLES)} Ekomforskriften-prinsipper initialisert.")


if __name__ == "__main__":
    print("Initialiserer Ekomforskriften-prinsipper...\n")
    asyncio.run(init_ekom_principles())
    print("\nFerdig!")
