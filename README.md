# PingAtlas 🌐

> Launch pings and traceroutes to real servers distributed around the world, build a latency map, detect suboptimal routes, and keep a historical record of how the network changes over time.

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
**Difficulty:** ⭐⭐⭐ Medium  
**Target audience:** Computer science students, network engineers, home lab enthusiasts.

---

## Features

- Raw ICMP probes via [Scapy](https://scapy.net/) — no OS-level `ping` subprocess dependency
- Traceroute with per-hop latency and geolocation
- Interactive world map (Leaflet + React) with latency colour scale (green → yellow → red)
- Suboptimal route detection based on configurable latency delta thresholds
- Historical time-series storage with per-destination trend charts
- Periodic scheduled probes (APScheduler)
- REST + WebSocket API (FastAPI)
- Fully containerised with Docker Compose

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  React Frontend (Vite)                              │
│  react-leaflet · Recharts · WebSocket client        │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP / WS
┌──────────────────────▼──────────────────────────────┐
│  FastAPI  (Uvicorn)                                 │
│  POST /probe  GET /results  GET /routes  WS /live   │
└────────┬────────────────────────┬───────────────────┘
         │                        │
┌────────▼──────────┐   ┌─────────▼─────────────────┐
│  Probe worker     │   │  PostgreSQL + TimescaleDB  │
│  Scapy ICMP       │   │  targets · hops · latency  │
│  GeoLite2 mmdb    │   └────────────────────────────┘
│  APScheduler      │
└───────────────────┘
```

Full architecture and data model documentation: [Wiki — Architecture & Stack](../../wiki/Architecture-and-Stack)

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Docker + Docker Compose | 24+ / v2+ | Required for containerised setup |
| Python | 3.11+ | Only needed for local development |
| Node.js | 20+ | Only needed for local frontend development |
| MaxMind GeoLite2 | — | Free licence required — see below |

### MaxMind GeoLite2 licence

PingAtlas uses the GeoLite2 City database for IP geolocation. You need a free MaxMind account to download the `.mmdb` file:

1. Register at <https://dev.maxmind.com/geoip/geolite2-free-geolocation-data>
2. Download `GeoLite2-City.mmdb`
3. Place the file at `backend/data/GeoLite2-City.mmdb`

> The file is excluded from version control (`.gitignore`). Never commit it to the repository.

---

## Quick start

```bash
# 1. Clone the repository
git clone https://github.com/your-username/pingatlas.git
cd pingatlas

# 2. Copy and configure environment variables
cp .env.example .env

# 3. Place your GeoLite2-City.mmdb inside backend/data/
cp /path/to/GeoLite2-City.mmdb backend/data/

# 4. Start all services
docker compose up --build

# 5. Open the application
open http://localhost:3000
```

The API will be available at `http://localhost:8000` and the auto-generated docs at `http://localhost:8000/docs`.

---

## Configuration

All runtime configuration is handled via environment variables. Copy `.env.example` to `.env` and adjust as needed.

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql://...` | PostgreSQL connection string |
| `PROBE_INTERVAL_SECONDS` | `300` | How often the scheduler runs probes |
| `PROBE_TARGETS` | _(see .env.example)_ | Comma-separated list of target hostnames/IPs |
| `LATENCY_ALERT_DELTA_MS` | `50` | Latency increase (ms) that triggers a suboptimal route alert |
| `MAX_HOPS` | `30` | Maximum TTL for traceroute probes |
| `GEOIP_DB_PATH` | `backend/data/GeoLite2-City.mmdb` | Path to the MaxMind database |

---

## API reference

Interactive documentation (Swagger UI) is auto-generated by FastAPI and available at `/docs` when the server is running. A brief summary:

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/probe` | Trigger an on-demand probe to a given target |
| `GET` | `/results` | List historical probe results (supports pagination and filtering) |
| `GET` | `/routes/{target}` | Return full traceroute polyline for a target |
| `GET` | `/targets` | List configured probe targets |
| `WS` | `/live` | WebSocket stream of real-time probe results |

Full API documentation: [Wiki — API Reference](../../wiki/API-Reference)

---

## Project structure

```
pingatlas/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routers
│   │   ├── core/         # Config, scheduler, startup
│   │   ├── db/           # SQLAlchemy models and migrations
│   │   ├── probe/        # Scapy ICMP engine + GeoIP wrapper
│   │   └── main.py
│   ├── data/             # GeoLite2 .mmdb (git-ignored)
│   ├── tests/
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/   # MapView, LatencyChart, Sidebar
│   │   ├── hooks/        # useProbe, useWebSocket
│   │   └── App.tsx
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Contributing

1. Fork the repository and create a feature branch: `git checkout -b feat/your-feature`
2. Follow the coding standards described in [CONTRIBUTING.md](CONTRIBUTING.md)
3. Run the test suite before opening a PR: `docker compose run --rm backend pytest`
4. Open a Pull Request against `main` — the PR template will guide you

---

## License

MIT — see [LICENSE](LICENSE) for details.