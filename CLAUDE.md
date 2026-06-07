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
- Run tests with coverage: `docker compose run --rm api pytest tests/ -v --cov=app/probe --cov-report=term-missing --cov-fail-under=80`
- probe/ package is at 100% coverage — maintain ≥80% on every PR
- CI: .github/workflows/ci.yml — jobs: lint (ruff + eslint), test-backend, build; triggers on push/PR to main

## Architecture
- backend/app/probe/ — Scapy ICMP engine + GeoIP wrapper (CAP_NET_RAW required)
- backend/app/probe/icmp_probe.py — ping(host, count, timeout) → list[float | None]
- backend/app/probe/traceroute.py — traceroute(host, max_hops, timeout) → list[Hop]; Hop(ttl, ip, rtt_ms)
- backend/app/probe/geoip.py — init() loads mmdb at startup; resolve(ip) → GeoResult(lat, lon, country, city)
- backend/app/api/  — FastAPI routers
- backend/app/api/schemas.py — Pydantic request/response models (ProbeRequest, ProbeOut, HopOut, PaginatedProbes)
- backend/app/api/probes.py — POST /probe (202), GET /results (paginated), GET /routes/{target_id}; _execute_probe(host) shared by HTTP handler and scheduler
- backend/app/api/ws.py — ConnectionManager + HopMessage schema + WebSocket /live endpoint
- backend/app/scheduler.py — AsyncIOScheduler; _probe_all_enabled() queries enabled targets each run; start()/stop() called from lifespan
- GET /routes/{target_id} returns latest traceroute as [[lat,lon],...] excluding null-coord hops; 404 if target missing
- WS /live broadcasts HopMessage per hop as traceroute runs; WebSocketDisconnect handled gracefully
- traceroute_stream() — async generator wrapping each sr1 call in run_in_executor for real-time yielding
- backend/app/db/   — SQLAlchemy models + Alembic migrations
- backend/app/db/session.py — async engine + AsyncSessionLocal
- backend/app/db/migrations/ — Alembic env + versioned migration scripts
- frontend/src/components/ — MapView, LatencyChart, Sidebar
- frontend/src/components/MapView.tsx — CircleMarkers (RTT colour: green<50ms, yellow<150ms, red≥150ms), Polylines per probe, Popups, real-time WS updates
- frontend/src/components/LatencyChart.tsx — Recharts LineChart, RTT over time, empty state when no probes
- frontend/src/components/Sidebar.tsx — target list (GET /api/targets), selected target summary (min/avg/max RTT), on-demand probe button (POST /probe), LatencyChart for selected target
- frontend/src/components/MapView.tsx — accepts selectedTargetId + refreshSignal; shows static route polyline (amber dashed) from useRoute, plus live WS CircleMarkers/Polylines
- frontend/src/hooks/useWebSocket.ts — connects to /live, filters hops with null lat/lon, returns HopMessage[]
- frontend/src/hooks/useProbeResults.ts — fetches GET /api/results?target=..., re-fetches on refreshSignal change
- frontend/src/hooks/useTargets.ts — fetches GET /api/targets, returns Target[]
- frontend/src/hooks/useRoute.ts — fetches GET /api/routes/{targetId}, returns [lat,lon][] for selected target
- Vite proxy: /api → http://api:8000, /live → ws://api:8000 (configured in vite.config.ts)
- App.tsx: lifts selectedTarget (Target | null) state; passes selectedTargetId+refreshSignal to MapView, onTargetChange+refreshSignal to Sidebar
- GET /api/targets endpoint added to probes.py; TargetOut schema in schemas.py (includes enabled field)
- PROBE_INTERVAL_SECONDS env var controls scheduler cadence (default 300 s); scheduler re-queries enabled targets on every tick

## Data model
- `targets` — hosts to probe (id UUID PK, host, label, enabled bool default TRUE, created_at)
- `probes` — each ping run (PK: id+started_at, target_id FK, rtt_ms, packet_loss) — TimescaleDB hypertable on started_at
- `hops` — traceroute hops (PK: id+started_at, probe_id, ttl, ip, lat/lon, city, country, asn) — TimescaleDB hypertable on started_at
- Hypertables require PrimaryKeyConstraint(id, started_at) — TimescaleDB constraint

## Important
- Never commit GeoLite2-City.mmdb (it's in .gitignore)
- Never use privileged: true in Docker — use cap_add: [NET_RAW] only
- DB port never exposed outside Docker network
- TimescaleDB hypertables: partition column must be part of the PK — always use composite PK (id, started_at) for time-series tables
- Scapy requires CAP_NET_RAW — already set in docker-compose.yml; tests must mock sr1, never send real packets
- geoip.init() must be called at app startup (FastAPI lifespan) — raises ConfigurationError if mmdb missing
- Private/loopback/reserved IPs always return all-None GeoResult without querying the reader
- TimescaleDB does not support FK constraints between hypertables — use primaryjoin with foreign() annotation in SQLAlchemy relationships
- geoip.init() failure is non-fatal in dev (logs warning); resolve() returns all-None if reader is not loaded