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
- backend/app/api/alerts.py — GET /alerts (query params: target_id, resolved)
- backend/app/api/ws.py — ConnectionManager + HopMessage schema + WebSocket /live endpoint
- backend/app/scheduler.py — AsyncIOScheduler; _probe_all_enabled() queries enabled targets each run; start()/stop() called from lifespan
- backend/app/anomaly.py — check_and_alert(session, target_id, probe_id, current_rtt): computes rolling avg of last 10 probes, creates Alert if delta > LATENCY_ALERT_DELTA_MS; optional POST to ALERT_WEBHOOK_URL
- backend/app/limiter.py — slowapi Limiter(key_func=get_remote_address, headers_enabled=True); POST /probe decorated with @limiter.limit("10/minute"); scheduler bypasses this (calls _execute_probe directly)
- backend/app/auth.py — require_api_key FastAPI dependency: reads API_KEYS env var (comma-separated), raises 401 if header missing or not in set; applied only to POST /probe via dependencies=[Depends(...)]
- GET /routes/{target_id} returns latest traceroute as [[lat,lon],...] excluding null-coord hops; 404 if target missing
- WS /live broadcasts HopMessage per hop as traceroute runs; WebSocketDisconnect handled gracefully
- traceroute_stream() — async generator wrapping each sr1 call in run_in_executor for real-time yielding
- backend/app/db/   — SQLAlchemy models + Alembic migrations
- backend/app/db/session.py — async engine + AsyncSessionLocal
- backend/app/db/migrations/ — Alembic env + versioned migration scripts
- frontend/src/components/MapView.tsx — CircleMarkers + Polylines from live WS; static route from useRoute (amber dashed) or selected probe hops (purple dashed); deduplicates identical coords (Docker NAT workaround); shows "No location data" banner when target IP is not in GeoIP DB
- frontend/src/components/LatencyChart.tsx — Recharts LineChart, RTT over time, empty state when no probes; selectedProbeId prop highlights selected dot in amber
- frontend/src/components/Sidebar.tsx — target list, RTT summary, on-demand probe button, LatencyChart (with selectedProbeId highlight), ProbeTimeline
- frontend/src/components/ProbeTimeline.tsx — horizontally scrollable colored bars (1 per probe, oldest→newest); red dot + hover tooltip for alerts; click sets selectedProbe in App
- frontend/src/hooks/useWebSocket.ts — connects to /live, filters hops with null lat/lon, returns HopMessage[]
- frontend/src/hooks/useProbeResults.ts — fetches GET /api/results?target=..., re-fetches on refreshSignal change; ProbeResult includes hops: HopOut[] for map route computation
- frontend/src/hooks/useTargets.ts — fetches GET /api/targets, returns Target[]
- frontend/src/hooks/useRoute.ts — fetches GET /api/routes/{targetId}, returns [lat,lon][] for selected target
- frontend/src/hooks/useAlerts.ts — fetches GET /api/alerts?target_id=..., returns Alert[]; used by Sidebar to pass alert markers to ProbeTimeline
- Vite proxy: /api → http://api:8000, /live → ws://api:8000 (configured in vite.config.ts)
- App.tsx: lifts selectedTarget (Target | null) + selectedProbe (ProbeResult | null) state; passes selectedTargetId+refreshSignal+selectedProbe to MapView, onTargetChange+onProbeSelect+refreshSignal to Sidebar
- GET /api/targets endpoint added to probes.py; TargetOut schema in schemas.py (includes enabled field)
- PROBE_INTERVAL_SECONDS env var controls scheduler cadence (default 300 s); scheduler re-queries enabled targets on every tick
- API_KEYS env var must be mapped in docker-compose.yml environment block (comma-separated keys for POST /probe auth)
- GEOIP_DB_PATH must be /app/GeoLite2-City.mmdb (volume mount is ./backend:/app; file lives at backend/GeoLite2-City.mmdb)
- Some public IPs (Cloudflare 1.1.1.1, Quad9 9.9.9.9) opt out of GeoIP databases — resolve() returns all-None, MapView shows "No location data" banner

## Data model
- `targets` — hosts to probe (id UUID PK, host, label, enabled bool default TRUE, created_at)
- `probes` — each ping run (PK: id+started_at, target_id FK, rtt_ms, packet_loss) — TimescaleDB hypertable on started_at
- `hops` — traceroute hops (PK: id+started_at, probe_id, ttl, ip, lat/lon, city, country, asn) — TimescaleDB hypertable on started_at
- `alerts` — latency spike alerts (id UUID PK, target_id FK, probe_id, triggered_at, rtt_ms, rolling_avg_ms, delta_ms, resolved bool default FALSE)
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