# PingAtlas

> Launch pings and traceroutes to servers distributed around the world, build a latency map, detect suboptimal routes, and keep a historical record of how the network changes over time.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18+-61DAFB?logo=react&logoColor=black)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Table of contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick start](#quick-start)
- [Configuration](#configuration)
- [API reference](#api-reference)
- [Project structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

PingAtlas is a self-hosted network diagnostics tool that probes a configurable set of target servers using ICMP (ping) and traceroute, geolocates every hop with MaxMind GeoLite2, and renders the results on an interactive world map. Latency history is persisted so you can see how routing changes over time.

**Estimated cost:** €0 — all dependencies are free/open-source.
**Target audience:** Computer science students, network engineers, home lab enthusiasts.

---

## Features

- Raw ICMP probes via [Scapy](https://scapy.net/) — no OS-level `ping` subprocess dependency
- Traceroute with per-hop latency and geolocation
- Interactive world map (Leaflet + React) with latency colour scale (green → yellow → red)
- Probe timeline panel showing RTT history with per-probe alert markers
- Suboptimal route detection based on configurable latency delta thresholds
- Historical time-series storage with per-destination trend charts
- Periodic scheduled probes (APScheduler)
- REST + WebSocket API (FastAPI) behind nginx reverse proxy
- Optional webhook notifications on latency spikes
- API key authentication for write endpoints
- Fully containerised with Docker Compose

---

## Architecture

```
Browser
  │ HTTP / WS  (port 80)
  ▼
┌─────────────────────────────────────────────────────┐
│  nginx reverse proxy                                │
│  /api/* → FastAPI   /live → WS   /* → Frontend     │
└────────────────────┬────────────────────────────────┘
                     │
       ┌─────────────┴─────────────┐
       ▼                           ▼
┌─────────────────┐   ┌────────────────────────────────┐
│  React (Vite)   │   │  FastAPI  (Uvicorn)             │
│  react-leaflet  │   │  POST /probe  GET /results      │
│  Recharts       │   │  GET /routes  GET /targets      │
│  WebSocket      │   │  GET /alerts  WS /live          │
└─────────────────┘   └──────────┬─────────────────────┘
                                 │
                    ┌────────────┴──────────────────┐
                    │                               │
          ┌─────────▼────────┐   ┌─────────────────▼──────────┐
          │  Probe engine    │   │  PostgreSQL 16 + TimescaleDB│
          │  Scapy ICMP      │   │  targets · probes · hops    │
          │  GeoLite2 mmdb   │   │  alerts                     │
          │  APScheduler     │   └────────────────────────────-┘
          └──────────────────┘
```

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Docker Engine | 24+ | Required |
| Docker Compose | v2+ | Bundled with Docker Desktop |
| MaxMind GeoLite2 | — | Free licence — see below |

### MaxMind GeoLite2 licence

PingAtlas uses the GeoLite2 City database for IP geolocation. A free MaxMind account is required:

1. Register at <https://dev.maxmind.com/geoip/geolite2-free-geolocation-data>
2. Download `GeoLite2-City.mmdb`
3. Place the file at `backend/GeoLite2-City.mmdb`

> The file is excluded from version control (`.gitignore`). Never commit it.

---

## Quick start

```bash
# 1. Clone the repository
git clone https://github.com/Adrigarsu/Ping-Atlas.git
cd Ping-Atlas

# 2. Copy and configure environment variables
cp .env.example .env
# Edit .env — at minimum set secure values for POSTGRES_PASSWORD and API_KEYS

# 3. Place your GeoLite2-City.mmdb at the backend root
cp /path/to/GeoLite2-City.mmdb backend/GeoLite2-City.mmdb

# 4. Start all services
docker compose up --build

# 5. Run database migrations (first run only)
docker compose run --rm api alembic upgrade head

# 6. Open the application
open http://localhost
```

The API is available at `http://localhost/api` and interactive docs at `http://localhost/api/docs`.

During development, direct ports are also exposed via `docker-compose.override.yml`:
- Frontend: `http://localhost:3000`
- API: `http://localhost:8000`

---

## Configuration

All runtime configuration is handled via environment variables. Copy `.env.example` to `.env` and adjust as needed. See `.env.example` for descriptions of every variable.

| Variable | Default | Description |
|---|---|---|
| `POSTGRES_USER` | `pingatlas` | PostgreSQL username |
| `POSTGRES_PASSWORD` | `changeme` | PostgreSQL password — change in production |
| `POSTGRES_DB` | `pingatlas` | PostgreSQL database name |
| `PROBE_INTERVAL_SECONDS` | `300` | How often the scheduler runs probes (seconds) |
| `PROBE_TARGETS` | `8.8.8.8,1.1.1.1,9.9.9.9` | Comma-separated initial probe targets |
| `LATENCY_ALERT_DELTA_MS` | `50` | RTT increase (ms) above rolling average that triggers an alert |
| `MAX_HOPS` | `30` | Maximum TTL for traceroute |
| `API_KEYS` | _(empty = disabled)_ | Comma-separated API keys for `POST /probe`. Leave empty to disable auth |
| `ALERT_WEBHOOK_URL` | _(unset)_ | Optional URL to POST alert payloads to on latency spikes |
| `GEOIP_DB_PATH` | `/app/GeoLite2-City.mmdb` | Path to GeoLite2 database inside the API container |

---

## API reference

Interactive Swagger UI is auto-generated by FastAPI and available at `http://localhost/api/docs`.

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/probe` | API key | Trigger an on-demand traceroute probe |
| `GET` | `/results` | — | List historical probe results (paginated) |
| `GET` | `/routes/{target_id}` | — | Latest traceroute polyline as `[[lat,lon],…]` |
| `GET` | `/targets` | — | List all probe targets |
| `GET` | `/alerts` | — | List latency spike alerts |
| `WS` | `/live` | — | Real-time hop stream during active probes |
| `GET` | `/health` | — | Liveness check |

---

## Project structure

```
Ping-Atlas/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routers (probes, alerts, ws)
│   │   ├── db/           # SQLAlchemy models + Alembic migrations
│   │   ├── probe/        # Scapy ICMP engine + GeoIP wrapper
│   │   ├── anomaly.py    # Latency spike detection + webhook
│   │   ├── auth.py       # API key dependency
│   │   ├── limiter.py    # slowapi rate limiter
│   │   ├── scheduler.py  # APScheduler periodic probes
│   │   └── main.py       # FastAPI app + lifespan
│   ├── tests/
│   ├── GeoLite2-City.mmdb  # (git-ignored — download separately)
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/   # MapView, Sidebar, LatencyChart, ProbeTimeline
│   │   ├── hooks/        # useProbeResults, useWebSocket, useRoute, useAlerts
│   │   └── App.tsx
│   ├── e2e/              # Playwright E2E tests
│   └── Dockerfile
├── nginx/
│   └── nginx.conf        # Reverse proxy config
├── wiki/
│   ├── Architecture-and-Stack.md
│   └── Roadmap.md
├── docker-compose.yml
├── docker-compose.override.yml   # Dev: exposes ports 3000 + 8000 directly
├── .env.example
├── CONTRIBUTING.md
└── README.md
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for coding standards, branch naming, and the PR process.

```bash
# Run backend tests
docker compose run --rm api pytest tests/ -v --cov=app/probe --cov-report=term-missing

# Run E2E tests (stack must be running)
cd frontend && npm run test:e2e

# Typecheck frontend
cd frontend && npx tsc --noEmit
```

---

## License

MIT — see [LICENSE](LICENSE) for details.