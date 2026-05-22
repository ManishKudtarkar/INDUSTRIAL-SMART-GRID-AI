# Industrial Smart Grid AI Architecture

## Runtime Flow

1. Substation clients stream newline-delimited JSON telemetry to the TCP server on port `9999`.
2. `server/socket_server.py` validates and stores the packet in memory through `TelemetryManager`.
3. The live AI pipeline runs point anomaly detection, sequence anomaly detection, health scoring, fault isolation, predictive models, alerting, and load redistribution.
4. `api/main.py` exposes the latest state through FastAPI on port `8000`.
5. The React dashboard polls `/state` every 1.5 seconds and renders the current grid state.

## Main Components

- `substations/`: USB, ADB, universal hardware, and simulated substation clients.
- `server/`: TCP socket server, connection handling, and telemetry state management.
- `ml/` and `ml_models/`: anomaly detection, health scoring, overload prediction, failure prediction, and load optimization.
- `smart_grid/`: load balancing, self-healing, relay/controller abstractions, and fault isolation.
- `alerts/`: in-memory alert management plus optional email, Slack, and SMS dispatch.
- `database/`: optional PostgreSQL persistence when `DB_URL` is configured.
- `api/`: FastAPI routes and service wrappers for dashboard and external clients.
- `dashboard/frontend/`: React/Vite live dashboard.
- `desktop/`: Electron wrapper for a local packaged app.

## State Model

The live system keeps operational state in memory for low-latency dashboard updates. If `DB_URL` is set, telemetry packets, health scores, alerts, and load snapshots are also written to PostgreSQL using `database/db_manager.py`.

## Deployment Modes

- Local Python: run the backend and clients directly.
- Docker demo: `docker-compose.yml` starts backend, frontend, and three simulated substations.
- Hardware mode: use `docker-compose.hardware.yml` to avoid simulated substations and stream from host-attached USB/ADB clients.
- Desktop: Electron starts the backend and simulated substations, then opens the built React dashboard.
