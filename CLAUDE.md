# PingAtlas

## Stack
- Backend: Python 3.11, FastAPI, SQLAlchemy 2 async, Alembic, Scapy, geoip2
- Frontend: React 18 + TypeScript, Vite, react-leaflet, Recharts
- DB: PostgreSQL 16 + TimescaleDB
- Infra: Docker Compose

## Commands
- `docker compose up --build` — start all services
- `docker compose run --rm api pytest -v` — run backend tests
- `cd frontend && npm run dev` — frontend dev server
- `cd frontend && tsc --noEmit` — typecheck frontend
- `docker compose run --rm api alembic upgrade head` — run migrations

## Conventions
- Conventional Commits: feat/fix/chore/db/test/docs/security + scope
- Branch naming: <type>/<issue-number>-<short-slug>  e.g. feat/3-icmp-probe
- Always close issues in commit footer: Closes #N
- Python: ruff for linting, black for formatting, type hints everywhere
- TypeScript: strict mode, no any, functional components with hooks
- Tests: pytest for backend (mock Scapy, no real ICMP), Playwright for E2E

## Architecture
- backend/app/probe/ — Scapy ICMP engine + GeoIP wrapper (CAP_NET_RAW required)
- backend/app/api/  — FastAPI routers
- backend/app/db/   — SQLAlchemy models + Alembic migrations
- frontend/src/components/ — MapView, LatencyChart, Sidebar

## Important
- Never commit GeoLite2-City.mmdb (it's in .gitignore)
- Never use privileged: true in Docker — use cap_add: [NET_RAW] only
- DB port never exposed outside Docker network