# NetROS

ROS-analyseverktøy (Risiko- og Sårbarhetsanalyse) for norske telekomselskaper, utviklet med fokus på Ekomforskriften og NSM Grunnprinsipper.

## Funksjoner

### Kjernefunksjonalitet
- **Asset Management** - Registrer og kategoriser verdier (kjernenett, aksessnett, transport, etc.)
- **Risikovurdering** - 5×5 matrise med nåværende og mål-vurdering
- **Tiltak** - Prioritering, ansvarlig, frist og status-tracking
- **Gjennomganger** - Periodiske, hendelsesbaserte og endringsbaserte revisjoner
- **Dokumenthåndtering** - Last opp og koble dokumenter til entiteter

### Compliance
- **NSM Grunnprinsipper** - Mapping av risikoer til NSMs 21 prinsipper
- **Ekomforskriften** - Samsvarssporing for §2-1 til §2-10
- **Rapporter** - PDF-generering for Nkom-rapportering

### Dashboard
- Risikomatrise-visualisering
- Tiltaksfremdrift
- Varsler for forfalte tiltak, kontraktsutløp, høye risikoer
- Gap-analyse for NSM/Ekomforskriften-dekning

## Teknologi

| Komponent | Teknologi |
|-----------|-----------|
| Backend | FastAPI + SQLAlchemy 2.0 (async) |
| Database | SQLite (utvikling) / PostgreSQL (produksjon) |
| Frontend | Jinja2 + HTMX + Tailwind CSS |
| Auth | JWT tokens i cookies |
| PDF | WeasyPrint |
| Container | Docker + Docker Compose |

## Installasjon

### Forutsetninger
- Python 3.11+
- pip

### Utvikling (SQLite)

```bash
# Klon repositoriet
git clone https://github.com/janogre/NET-ROS.git
cd NET-ROS

# Opprett virtuelt miljø
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Installer avhengigheter
pip install -e .

# Kopier miljøvariabler
cp .env.example .env

# Initialiser database
alembic upgrade head

# Seed NSM-prinsipper og Ekomforskriften
python scripts/init_nsm_principles.py
python scripts/init_ekomforskriften.py

# Opprett admin-bruker
python scripts/create_admin.py

# Start utviklingsserver
uvicorn app.main:app --reload
```

Applikasjonen er tilgjengelig på http://localhost:8000

### Produksjon (Docker)

```bash
# Start med Docker Compose
docker-compose up -d

# Se logger
docker-compose logs -f netros

# Stopp
docker-compose down
```

## API-dokumentasjon

Når serveren kjører, er API-dokumentasjonen tilgjengelig på:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Hovedendepunkter

| Prefix | Beskrivelse |
|--------|-------------|
| `/api/v1/auth` | Autentisering |
| `/api/v1/users` | Brukerhåndtering |
| `/api/v1/projects` | ROS-prosjekter |
| `/api/v1/assets` | Fysiske verdier |
| `/api/v1/information-assets` | Informasjonsverdier |
| `/api/v1/suppliers` | Leverandører |
| `/api/v1/risks` | Risikoer |
| `/api/v1/actions` | Tiltak |
| `/api/v1/reviews` | Gjennomganger |
| `/api/v1/documents` | Dokumenter |
| `/api/v1/ekomforskriften` | Ekomforskriften-samsvar |
| `/api/v1/dashboard` | Dashboard-data |
| `/api/v1/reports` | Rapporter |

## Rollebasert tilgang (RBAC)

| Rolle | Rettigheter |
|-------|-------------|
| `admin` | Full tilgang |
| `risikoansvarlig` | CRUD alle risikoer/tiltak |
| `bruker` | CRUD egne risikoer |
| `leser` | Kun lesetilgang |

## Risikomatrise

5×5 matrise (sannsynlighet × konsekvens) med fargekoder:

| Score | Nivå | Farge |
|-------|------|-------|
| 1-4 | Akseptabel | Grønn |
| 5-9 | Lav | Gul |
| 10-16 | Middels | Oransje |
| 17-25 | Høy | Rød |

## Prosjektstruktur

```
netros/
├── alembic/                  # Database-migrasjoner
├── app/
│   ├── api/v1/               # REST API-endepunkter
│   ├── core/                 # Auth, dependencies
│   ├── models/               # SQLAlchemy ORM-modeller
│   ├── schemas/              # Pydantic request/response
│   ├── services/             # Forretningslogikk
│   └── templates/            # Jinja2 + HTMX (norsk UI)
├── scripts/                  # Admin-scripts
├── static/                   # CSS, JavaScript
├── tests/                    # Pytest
├── docker-compose.yml
└── pyproject.toml
```

## Miljøvariabler

Se `.env.example` for alle tilgjengelige variabler:

```env
DATABASE_URL=sqlite+aiosqlite:///./netros.db
SECRET_KEY=endre-denne-i-produksjon
DEBUG=true
```

## Lisens

Proprietær - NEAS AS

## Bidrag

Interne bidrag velkommen. Kontakt utviklingsteamet for tilgang.
