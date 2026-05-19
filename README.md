# ⚡ Industrial Smart Grid AI

> A distributed AI-powered smart grid simulation and monitoring system. Multiple devices act as virtual electrical substations streaming real-time telemetry to a central AI server that detects anomalies, scores health, balances load, and displays everything on a live dashboard.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Data Sources](#data-sources)
- [Quick Start](#quick-start)
- [Distributed Multi-Device Setup](#distributed-multi-device-setup)
- [Features](#features)
- [API Reference](#api-reference)
- [Dashboard](#dashboard)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Alert Channels](#alert-channels)
- [Docker](#docker)

---

## Overview

This system simulates a real industrial smart grid where:

- **Substation devices** (laptops, Android phones via ADB, Arduino/ESP32 via USB) continuously stream electrical telemetry
- **AI server** receives all streams, runs anomaly detection, calculates health scores, isolates faults, and redistributes load
- **React dashboard** displays everything live with charts, status cards, and alerts
- **Self-healing engine** automatically restores load to recovering substations

The architecture mirrors a real-world predictive maintenance and SCADA monitoring platform.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     DATA SOURCES                                │
│                                                                 │
│  📱 Android Phone    🔌 Arduino/ESP32    💻 Laptop Simulator    │
│  (ADB via USB)       (Serial/COM port)   (--simulate flag)      │
│       │                    │                    │               │
│       └────────────────────┴────────────────────┘               │
│                            │ TCP JSON stream                    │
│                            │ port 9999                          │
└────────────────────────────┼────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AI SERVER (main laptop)                      │
│                                                                 │
│  server/socket_server.py                                        │
│       │                                                         │
│       ├── Feature Engineering (42 features)                     │
│       │     statistical, harmonic, FFT, phase unbalance         │
│       │                                                         │
│       ├── Anomaly Detection                                     │
│       │     IsolationForest (sklearn)                           │
│       │                                                         │
│       ├── Health Scoring (0–100)                                │
│       │     rule-based penalties + ML anomaly flag              │
│       │                                                         │
│       ├── Fault Isolation                                       │
│       │     6 fault types, severity classification              │
│       │                                                         │
│       ├── Load Balancing                                        │
│       │     auto-redistribution on critical state               │
│       │                                                         │
│       ├── Self-Healing Engine                                   │
│       │     gradual load recovery after health improves         │
│       │                                                         │
│       └── Alert Manager                                         │
│             Email / Slack / SMS dispatch                        │
│                                                                 │
│  FastAPI REST API (port 8000)                                   │
│       └── 21 endpoints across 5 route groups                   │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DASHBOARDS                                 │
│                                                                 │
│  React + Vite + Tailwind + Recharts  →  http://localhost:5173   │
│  Streamlit (fallback)                →  http://localhost:8501   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Sources

The system supports three real hardware sources and one simulation mode.

### 📱 Android Phone via ADB (USB Debugging)

Reads real sensor data from your phone over USB:

| Phone Sensor | Grid Field | Mapping |
|---|---|---|
| Battery voltage (mV) | `voltage` | 3.3–4.2V → 200–245V (scaled) |
| Battery temperature (°C) | `temperature` | Direct (real value) |
| Battery level (%) | `load_percentage` | Direct (real value) |
| CPU usage (%) | `current` | 0–100% CPU → 10–20A |
| Charging state | `harmonic_5th` | AC=1.5%, USB=3.0%, Discharging=5.5% |

**Setup:**
1. Enable USB Debugging on your phone: `Settings → Developer Options → USB Debugging`
2. Connect phone via USB cable
3. Accept the "Allow USB Debugging" prompt on the phone

```bash
python substations/substation_client.py --id S1 --source adb
```

### 🔌 Arduino / ESP32 / Microcontroller via USB Serial

Your microcontroller sends newline-terminated JSON at 9600 baud:

```json
{"voltage": 230.1, "current": 15.2, "temperature": 60.5, "harmonic_5th": 2.1, "load_percentage": 45.0}
```

Any subset of fields is accepted — missing fields are handled gracefully.

```bash
# Auto-detect COM port:
python substations/substation_client.py --id S1

# Specify port explicitly:
python substations/substation_client.py --id S1 --port-name COM3
python substations/substation_client.py --id S1 --port-name /dev/ttyUSB0

# List available ports:
python substations/substation_client.py --list-ports
```

### 💻 Simulation Mode (no hardware required)

Generates realistic synthetic telemetry with Gaussian noise and sinusoidal load drift. Only use this for demos or development.

```bash
python substations/substation_client.py --id S1 --simulate
python substations/substation_client.py --id S2 --simulate --faulty   # with fault injection
```

---

## Quick Start

### Single machine (all components on one laptop)

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Install frontend dependencies
cd dashboard/frontend && npm install && cd ../..

# 3a. Start with real USB sensor (default)
python start_all.py

# 3b. Start with Android phone
python start_all.py   # then run ADB client separately:
python substations/substation_client.py --id S1 --source adb

# 3c. Start in simulation mode (demo, no hardware)
python start_all.py --simulate
```

Then open:
- **React Dashboard** → http://localhost:5173
- **API Docs (Swagger)** → http://localhost:8000/docs
- **Streamlit Dashboard** → http://localhost:8501

---

## Distributed Multi-Device Setup

Run each substation on a separate device connected to the same WiFi network.

### On the AI Server Laptop

```bash
pip install -r requirements.txt
python api/main.py
# Note your IP address, e.g. 192.168.1.100
```

### On each Substation Device

```bash
# Laptop with USB sensor:
python substations/substation_client.py --id S1 --host 192.168.1.100

# Laptop with Android phone:
python substations/substation_client.py --id S2 --host 192.168.1.100 --source adb

# Laptop in simulation:
python substations/substation_client.py --id S3 --host 192.168.1.100 --simulate
```

### Start Dashboard on Server Laptop

```bash
cd dashboard/frontend && npm run dev
```

---

## Features

### Real-Time Telemetry Streaming

- TCP socket server accepts unlimited concurrent substation connections
- Newline-delimited JSON protocol, 1–2 second intervals
- Thread-safe state store with 20-point rolling history per substation
- Automatic reconnection on disconnect (client-side)
- Partial sensor data supported — missing fields handled gracefully

### AI Anomaly Detection

- **Model:** Isolation Forest (scikit-learn)
- Trained on 500 synthetic normal samples at startup
- 5 input features: voltage, current, temperature, harmonic_5th, load_percentage
- Phone battery voltage automatically neutralised to prevent false positives
- Returns binary anomaly flag + raw anomaly score

### Health Score System (0–100)

Calculated per packet with rule-based penalties:

| Condition | Penalty |
|---|---|
| Temperature > 85°C | −1.5 × (temp − 85) |
| Voltage outside 200–250V | −20 points |
| Harmonics > 8% | −3 × (harmonic − 8), max −30 |
| Load > 80% | −0.5 × (load − 80) |
| ML anomaly detected | −30 points |

| Score | Status |
|---|---|
| 80–100 | 🟢 Healthy |
| 50–79 | 🟠 Warning |
| 0–49 | 🔴 Critical |

### Feature Engineering (42 features)

Extracted from raw telemetry + rolling history window:

- **Statistical:** mean, std, min, max, range, rate-of-change per metric
- **Harmonic analysis:** THD approximation, power factor estimate, severity index
- **Phase unbalance:** NEMA unbalance %, voltage instability coefficient
- **FFT analysis:** dominant frequency magnitude, spectral entropy

### Fault Isolation

Rule-based engine classifying 6 fault types:

| Fault | Trigger Condition | Severity |
|---|---|---|
| Overheat | Temperature > 85°C | HIGH |
| Voltage Sag | Voltage < 205V | HIGH |
| Voltage Surge | Voltage > 255V | MEDIUM |
| Overload | Load > 80% | HIGH |
| Harmonic Distortion | Harmonics > 8% | MEDIUM |
| Overcurrent | Current > 25A | HIGH |

### Smart Load Redistribution

Automatic load balancing triggered when any substation goes Critical:

```
Normal:    S1=33%  S2=33%  S3=33%
S2 Critical: S1=45%  S2=10%  S3=45%
```

- Critical substations receive minimum 10% load floor
- Healthy substations share remaining load equally
- Rebalances on every telemetry packet

### Self-Healing Engine

Background thread that gradually restores load to recovering substations:

- Monitors health score every 10 seconds
- Recovery begins when health score rises above 70
- Load restored in 5% increments per cycle
- Stops when substation reaches its fair share
- Pauses immediately if health drops again

### Explainability

- **SHAP TreeExplainer** — feature contributions for each anomaly prediction
- **Permutation importance** — which features most affect anomaly detection rate
- **Root cause engine** — knowledge base mapping fault types to probable causes with likelihood scores and recommended actions

### Alert System

Three severity levels: `CRITICAL`, `WARNING`, `INFO`

Triggers:
- Health score drops to Critical (with 30-second cooldown per substation)
- Health degrades from Healthy → Warning
- Substation recovers from Critical/Warning → Healthy

Notification channels (configured via `.env`):
- **Email** — SMTP (Gmail, Outlook, any provider)
- **Slack** — Incoming Webhook
- **SMS** — Twilio REST API

### USB Device Detection

- `/usb/status` endpoint scans COM ports in real-time
- Dashboard shows each port with animated pulse ring when streaming
- Shows which substation ID is assigned to each port

---

## API Reference

Base URL: `http://localhost:8000`

Interactive docs: http://localhost:8000/docs

### System

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Health check |
| GET | `/state` | Full grid state snapshot (polled by dashboard) |
| GET | `/summary` | System health summary |

### Telemetry

| Method | Endpoint | Description |
|---|---|---|
| GET | `/telemetry/` | Latest telemetry for all substations |
| GET | `/telemetry/{sub_id}` | Latest telemetry for one substation |
| GET | `/telemetry/{sub_id}/history` | Rolling history (last 20 packets) |

### Anomaly & Health

| Method | Endpoint | Description |
|---|---|---|
| GET | `/anomaly/health` | Health scores for all substations |
| GET | `/anomaly/health/{sub_id}` | Health score for one substation |
| GET | `/anomaly/summary` | Overall system health summary |
| GET | `/anomaly/faults` | Fault reports for all substations |
| GET | `/anomaly/faults/{sub_id}` | Fault report for one substation |

### Load Balancing

| Method | Endpoint | Description |
|---|---|---|
| GET | `/load/distribution` | Current load distribution |
| GET | `/load/substations` | List of active substations |
| POST | `/load/rebalance` | Trigger manual rebalance |

### Prediction & Explainability

| Method | Endpoint | Description |
|---|---|---|
| POST | `/predict/anomaly` | On-demand anomaly prediction for a packet |
| POST | `/predict/root-cause` | Root cause analysis for a packet |
| GET | `/predict/model-info` | Active ML model information |

### Alerts

| Method | Endpoint | Description |
|---|---|---|
| GET | `/alerts` | Alert feed (latest 20) |
| GET | `/alerts/{sub_id}` | Alerts for one substation |
| DELETE | `/alerts` | Clear all alerts |

### USB

| Method | Endpoint | Description |
|---|---|---|
| GET | `/usb/status` | Connected USB devices + active substations |
| GET | `/usb/ports` | List all available COM/serial ports |

---

## Dashboard

### React Dashboard (primary) — http://localhost:5173

Built with React 19, Vite, Tailwind CSS, Recharts.

**Overview Tab**
- System health banner (Healthy / Warning / Critical)
- USB device panel with live port status and animated pulse rings
- Per-substation cards showing:
  - Health score ring (animated, color-coded)
  - Data source badge (📱 Android ADB / 🔌 USB Sensor / ⚙ Simulated)
  - All sensor metrics with threshold-based color warnings
  - Anomaly detected badge (blinking)
  - Phone raw data strip (battery V, temp, level) when using ADB
  - Load bar with actual vs target
  - Fault type badges (HIGH = red, MEDIUM = yellow)
- Load distribution bar chart with stat cards
- Live alert feed

**Live Trends Tab**
- 4 scrolling line charts (60-point history):
  - Temperature with 75°C warn / 85°C danger reference lines
  - Voltage with 245V warn / 250V danger reference lines
  - Load % with 60% warn / 80% danger reference lines
  - Health Score with 50 warn / 30 danger reference lines

**Load Balance Tab**
- Bar chart of current load distribution
- Detailed table: actual load vs target vs status per substation

**Alerts Tab**
- Full alert feed with CRITICAL / WARNING / INFO styling

### Streamlit Dashboard (fallback) — http://localhost:8501

Simpler Python-based dashboard. Polls `/state` every 1.5 seconds. Shows substation cards, load bar chart, trend charts (4 tabs), and alert feed.

---

## Project Structure

```
industrial-smart-grid-ai/
│
├── substations/                    # Substation clients (run on each device)
│   ├── substation_client.py        # Main entry point — routes to correct source
│   ├── usb_substation_client.py    # USB serial client (Arduino/ESP32)
│   ├── adb_substation_client.py    # Android phone via ADB
│   ├── universal_hw_client.py      # Auto-detects ADB or serial
│   ├── telemetry_generator.py      # Synthetic telemetry with drift
│   └── fault_simulator.py          # 5 fault types for simulation
│
├── server/                         # AI server core
│   ├── socket_server.py            # TCP server + full AI pipeline
│   ├── telemetry_manager.py        # Thread-safe state + history store
│   └── connection_handler.py       # Per-client connection handler
│
├── ml/                             # Machine learning
│   ├── anomaly_detector.py         # IsolationForest anomaly detection
│   └── health_score.py             # Health score calculation (0–100)
│
├── ml_models/                      # Advanced ML (wired in optionally)
│   └── anomaly_detection/
│       └── advanced_lstm_autoencoder.py   # LSTM Autoencoder (TensorFlow)
│
├── smart_grid/                     # Grid control logic
│   ├── load_balancer.py            # Automatic load redistribution
│   ├── self_healing_engine.py      # Gradual load recovery
│   ├── fault_isolation.py          # Rule-based fault classification
│   └── substation_manager.py       # Aggregated state manager
│
├── feature_engineering/            # Feature extraction (42 features)
│   ├── feature_pipeline.py         # Orchestrator
│   ├── statistical_features.py     # Mean, std, rate-of-change
│   ├── harmonic_analysis.py        # THD, power factor
│   ├── phase_unbalance.py          # Voltage instability
│   └── fft_analysis.py             # Frequency-domain features
│
├── alerts/                         # Alert system
│   ├── alert_manager.py            # Thread-safe store + dispatch
│   ├── email_alert.py              # SMTP email
│   ├── slack_alert.py              # Slack webhook
│   ├── sms_alert.py                # Twilio SMS
│   └── critical_shutdown.py        # Emergency shutdown protocol
│
├── explainability/                 # AI explainability
│   ├── shap_explainer.py           # SHAP feature contributions
│   ├── feature_importance.py       # Permutation importance
│   └── root_cause_engine.py        # Root cause + recommendations
│
├── api/                            # FastAPI backend
│   ├── main.py                     # App + router registration
│   ├── routes/                     # 5 route groups (21 endpoints)
│   │   ├── telemetry_routes.py
│   │   ├── anomaly_routes.py
│   │   ├── load_balancing_routes.py
│   │   ├── prediction_routes.py
│   │   └── usb_routes.py
│   ├── services/                   # Business logic
│   │   ├── smart_grid_service.py
│   │   ├── prediction_service.py
│   │   └── alert_service.py
│   └── schemas/                    # Pydantic models
│       ├── telemetry_schema.py
│       ├── fault_schema.py
│       └── response_schema.py
│
├── dashboard/
│   ├── app.py                      # Streamlit dashboard
│   └── frontend/                   # React dashboard
│       └── src/
│           ├── App.jsx             # Main app + data polling
│           └── components/
│               ├── SubstationCard.jsx    # Live metric card
│               ├── LiveChart.jsx         # Scrolling line chart
│               ├── LoadDistribution.jsx  # Load bar chart
│               ├── AlertFeed.jsx         # Alert log
│               ├── SystemBanner.jsx      # Status banner
│               └── UsbStatus.jsx         # USB device panel
│
├── database/
│   ├── db_manager.py               # Optional PostgreSQL persistence
│   └── schema.sql                  # Tables: telemetry, health, alerts, load
│
├── monitoring/
│   └── metrics_collector.py        # Prometheus metrics (optional)
│
├── shared/
│   ├── config.py                   # All tuneable parameters
│   ├── schemas.py                  # Shared Pydantic models
│   └── utils.py                    # Logging, validation helpers
│
├── start_all.py                    # Single-machine launcher
├── list_usb_ports.py               # Utility: list COM ports
├── setup_adb.py                    # Utility: download ADB
├── requirements.txt
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
└── .env                            # Credentials (never committed)
```

---

## Configuration

All parameters are in `shared/config.py`. Key settings:

```python
# Network
SERVER_PORT = 9999          # TCP socket for telemetry
API_PORT    = 8000          # FastAPI REST

# Normal operating ranges
VOLTAGE_MIN = 220.0         # V
VOLTAGE_MAX = 240.0
TEMP_MAX    = 75.0          # °C
LOAD_MAX    = 60.0          # %

# Health scoring
HEALTH_HEALTHY_MIN = 80     # score ≥ 80 → Healthy
HEALTH_WARNING_MIN = 50     # score ≥ 50 → Warning

# Load balancing
CRITICAL_LOAD_FLOOR = 10.0  # minimum load for critical substation

# Self-healing
RECOVERY_THRESHOLD = 70     # health score to start recovery
RECOVERY_STEP      = 5.0    # % load restored per cycle
HEALING_INTERVAL   = 10     # seconds between healing checks

# Alerts
ALERT_COOLDOWN_SEC = 30     # minimum seconds between same-substation alerts
```

---

## Alert Channels

Set credentials in `.env` — channels are silently skipped if not configured.

```env
# Email (SMTP)
ALERT_EMAIL_FROM=sender@gmail.com
ALERT_EMAIL_TO=ops@yourcompany.com
ALERT_EMAIL_PASSWORD=your_app_password
ALERT_SMTP_HOST=smtp.gmail.com
ALERT_SMTP_PORT=587

# Slack
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T.../B.../...

# SMS (Twilio)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_FROM_NUMBER=+1xxxxxxxxxx
TWILIO_TO_NUMBER=+1xxxxxxxxxx
```

---

## Docker

```bash
# Build and start backend + frontend
docker-compose up --build

# Services:
#   backend  → http://localhost:8000  (API + socket server)
#   frontend → http://localhost:5173  (React dashboard)
```

Then run substation clients on other devices pointing to the server IP.

---

## Fault Types Simulated

| Fault | Trigger | Symptoms |
|---|---|---|
| Overheat | Temperature > 100°C | Transformer/equipment overheating |
| Overload | Load > 85%, Current > 22A | Demand spike or load transfer |
| Voltage Sag | Voltage 170–190V | Upstream fault or heavy load |
| Harmonic Distortion | Harmonics > 10% | Non-linear loads, VFDs |
| Combined | All of the above | Worst-case multi-fault scenario |

---

## Telemetry Packet Format

```json
{
  "substation_id":   "S1",
  "timestamp":       "2026-05-19T22:00:00.000000",
  "voltage":         230.5,
  "current":         14.2,
  "temperature":     62.1,
  "harmonic_5th":    3.5,
  "load_percentage": 35.0
}
```

Fields may be `null` for sensors that don't measure every metric. The AI pipeline handles partial data gracefully.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Substation clients | Python, pyserial, ADB |
| Communication | TCP sockets (JSON over newline-delimited stream) |
| AI / ML | scikit-learn (IsolationForest), numpy |
| Advanced ML | TensorFlow / Keras (LSTM Autoencoder) |
| Explainability | SHAP, permutation importance |
| Backend API | FastAPI, uvicorn, Pydantic |
| Frontend | React 19, Vite, Tailwind CSS, Recharts |
| Alt dashboard | Streamlit |
| Database | PostgreSQL / TimescaleDB (optional) |
| Monitoring | Prometheus (optional) |
| Deployment | Docker, docker-compose |
