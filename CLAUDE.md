# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Status

NetROS MVP implementert - ROS-analyseverktøy for NEAS med:
- Brukerautentisering med RBAC
- Asset management med kategorier og kritikalitet
- Risikovurdering med 5×5 matrise (nåværende + mål)
- Tiltak med prioritet, status og frist
- NSM Grunnprinsipper mapping
- PDF-rapportgenerering
- Norsk UI med HTMX

## Build Commands

### Utvikling (SQLite)

```bash
# Installer avhengigheter
pip install -e .

# Initialiser database og seed NSM-prinsipper
python scripts/init_nsm_principles.py

# Opprett admin-bruker
python scripts/create_admin.py

# Start utviklingsserver
uvicorn app.main:app --reload

# Kjør tester
pytest
```

### Produksjon (Docker)

```bash
# Start med Docker Compose
docker-compose up -d

# Se logger
docker-compose logs -f netros

# Stopp
docker-compose down
```

## Architecture

### Prosjektstruktur

```
netros/
├── alembic/                  # Database migrations
├── app/
│   ├── main.py               # FastAPI entry point + web routes
│   ├── config.py             # Pydantic Settings (.env)
│   ├── database.py           # SQLAlchemy async session
│   ├── models/               # SQLAlchemy ORM models
│   ├── schemas/              # Pydantic request/response schemas
│   ├── api/v1/               # REST API endpoints
│   ├── services/             # Business logic (risk_service, report_service)
│   ├── core/                 # Security, dependencies, auth
│   └── templates/            # Jinja2 + HTMX templates (norsk)
├── static/                   # CSS, JavaScript
├── scripts/                  # Admin scripts
├── tests/
├── docker-compose.yml
└── pyproject.toml
```

### Teknologier

| Komponent | Teknologi |
|-----------|-----------|
| Backend | FastAPI + SQLAlchemy 2.0 (async) |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Frontend | Jinja2 + HTMX + Tailwind CSS |
| Auth | JWT tokens i cookies (session-basert) |
| PDF | WeasyPrint |

### Hovedmodeller

- **User**: Brukere med roller (admin, risikoansvarlig, bruker, leser)
- **Project**: ROS-prosjekter (periodisk, hendelsesbasert, DPIA)
- **Asset**: Verdier med kategorier (kjernenett, aksessnett, etc.) og kritikalitet (1-5)
- **Risk**: Risikoer med sannsynlighet × konsekvens matrise
- **Action**: Tiltak med prioritet og status
- **NSMPrinciple**: Referansedata for NSM Grunnprinsipper

### API Struktur

- `GET/POST /api/v1/assets` - CRUD assets
- `GET/POST /api/v1/risks` - CRUD risikoer
- `GET /api/v1/risks/matrix` - Risikomatrise-data
- `GET/POST /api/v1/actions` - CRUD tiltak
- `GET /api/v1/dashboard/summary` - Dashboard-data
- `GET /api/v1/reports/risk-register` - HTML rapport
- `GET /api/v1/reports/risk-register/pdf` - PDF rapport

### Rollebasert tilgang (RBAC)

| Rolle | Rettigheter |
|-------|-------------|
| admin | Full tilgang |
| risikoansvarlig | CRUD alle risikoer/tiltak |
| bruker | CRUD egne risikoer |
| leser | Kun lesetilgang |

### Risikomatrise

5×5 matrise med fargekoder:
- **Grønn (1-4)**: Akseptabel
- **Gul (5-9)**: Lav
- **Oransje (10-16)**: Middels
- **Rød (17-25)**: Høy
