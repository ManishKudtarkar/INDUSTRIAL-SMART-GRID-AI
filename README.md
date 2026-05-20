# ⚡ Industrial Smart Grid AI

> A distributed AI-powered smart grid simulation and real-time monitoring system.
> Multiple devices stream live electrical telemetry to a central AI server that runs
> anomaly detection, health scoring, fault isolation, predictive maintenance, and
> automatic load balancing — all displayed on a live React dashboard.

[![Python](https://img.shields.io/badge/Python-3.14.3-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.136.1-green)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB)](https://react.dev)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.8.0-orange)](https://scikit-learn.org)

---

## Table of Contents

1. [What This System Does](#1-what-this-system-does)
2. [End-to-End System Flow](#2-end-to-end-system-flow)
3. [System Architecture](#3-system-architecture)
4. [Data Sources — Where S1/S2/S3 Data Comes From](#4-data-sources)
5. [Communication Protocol](#5-communication-protocol)
6. [AI Pipeline — Step by Step](#6-ai-pipeline)
7. [All ML Models](#7-all-ml-models)
8. [Health Score System](#8-health-score-system)
9. [Load Balancing & Self-Healing](#9-load-balancing--self-healing)
10. [Alert System](#10-alert-system)
11. [Quick Start](#11-quick-start)
12. [Distributed Multi-Device Setup](#12-distributed-multi-device-setup)
13. [Android Phone via ADB — Step by Step](#13-android-phone-via-adb)
14. [Arduino / ESP32 via USB — Step by Step](#14-arduino--esp32-via-usb)
15. [API Reference](#15-api-reference)
16. [Dashboard](#16-dashboard)
17. [Project Structure](#17-project-structure)
18. [Configuration](#18-configuration)
19. [Docker Deployment](#19-docker-deployment)
20. [Tech Stack](#20-tech-stack)

---

## 1. What This System Does

This project simulates a real industrial smart grid where multiple devices act as virtual electrical substations. Each device streams live sensor data to a central AI server that:

- Detects anomalies using **IsolationForest** (point-based) and **LSTM** (sequence/trend-based)
- Calculates a **health score (0–100)** for each substation every 1.5 seconds
- Classifies **fault types** (overheat, voltage sag, overload, harmonics, overcurrent)
- **Predicts overload** risk in the next 5 readings using RandomForest
- **Predicts transformer failure** probability over 24 hours using Logistic Regression
- **Automatically redistributes load** away from failing substations
- **Self-heals** by gradually restoring load as substations recover
- Sends **Email / Slack / SMS alerts** on critical events
- Displays everything on a **live React dashboard** with real-time charts

Think of it as a miniature SCADA + predictive maintenance platform.

---

## 2. End-to-End System Flow

```mermaid
flowchart TD
    A[📱 Android Phone\nUSB + ADB] -->|Real battery V/T/level| D
    B[🔌 Arduino/ESP32\nUSB Serial COM port] -->|Real sensor JSON| D
    C[💻 Laptop Simulator\n--simulate flag] -->|Synthetic telemetry| D

    D[TCP Socket\nport 9999\nnewline-delimited JSON] --> E

    E[server/socket_server.py\nReceives all streams] --> F

    subgraph AI_PIPELINE [AI Pipeline — runs on every packet]
        F[Step 1: Validate & Store\nTelemetryManager] --> G
        G[Step 2: Feature Engineering\n42 features extracted] --> H
        H[Step 3: IsolationForest\nPoint anomaly detection] --> I
        I[Step 4: LSTM Detector\nSequence/trend anomaly] --> J
        J[Step 5: Health Score\n0-100 with penalties] --> K
        K[Step 6: Fault Isolation\n6 fault types classified] --> L
        L[Step 7: Overload Predictor\nNext-5-readings risk] --> M
        M[Step 8: Failure Predictor\n24-hour probability] --> N
        N[Step 9: Load Redistribution\nRedistributionEngine] --> O
        O[Step 10: Self-Healing\nGradual load recovery] --> P
        P[Step 11: Alert Dispatch\nEmail + Slack + SMS]
    end

    P --> Q[FastAPI REST API\nport 8000\n25 endpoints]
    Q --> R[React Dashboard\nlocalhost:5173\nPolls every 1.5s]
    Q --> S[Streamlit Dashboard\nlocalhost:8501\nFallback]
```

---

## 3. System Architecture

```mermaid
graph TB
    subgraph DEVICES [Substation Devices]
        D1[Laptop 1\nSubstation S1\nHealthy]
        D2[Android Phone\nSubstation S2\nReal ADB data]
        D3[Arduino/ESP32\nSubstation S3\nReal sensors]
    end

    subgraph SERVER [AI Server - Main Laptop]
        SS[socket_server.py\nTCP port 9999]
        TM[TelemetryManager\nRolling history per sub]
        FE[Feature Engineering\n42 features]

        subgraph ML [ML Models - ml_models/]
            IF[IsolationForest\nPoint anomaly]
            LSTM[LSTM Detector\nSequence anomaly]
            HS[HealthScoreModel\nGradientBoosting]
            OP[OverloadPredictor\nRandomForest]
            FP[FailurePredictor\nLogisticRegression]
            LO[LoadOptimizer\nWeighted allocation]
        end

        subgraph GRID [Smart Grid Logic]
            RE[RedistributionEngine\nSmooth transitions]
            SH[SelfHealingEngine\nGradual recovery]
            FI[FaultIsolation\n6 fault types]
        end

        AM[AlertManager\nEmail+Slack+SMS]
        API[FastAPI\nport 8000\n25 endpoints]
    end

    subgraph DASH [Dashboards]
        RD[React Dashboard\nlocalhost:5173]
        ST[Streamlit\nlocalhost:8501]
    end

    D1 -->|TCP JSON 1.5s| SS
    D2 -->|TCP JSON 2s| SS
    D3 -->|TCP JSON 1.5s| SS

    SS --> TM
    TM --> FE
    FE --> IF
    FE --> LSTM
    IF --> HS
    LSTM --> HS
    HS --> FI
    FI --> OP
    OP --> FP
    FP --> RE
    RE --> SH
    SH --> AM
    AM --> API
    HS --> API
    FI --> API
    OP --> API
    FP --> API

    API -->|GET /state every 1.5s| RD
    API -->|GET /state every 1.5s| ST
```

---

## 4. Data Sources

**S1, S2, S3 are substation IDs** — labels you assign to each device. The actual data comes from whichever hardware you connect.

```mermaid
graph LR
    subgraph PHONE [Android Phone via ADB]
        P1[Battery Voltage mV] -->|÷1000 then scale\n3.3-4.2V → 200-245V| V[voltage field]
        P2[Battery Temperature\ndecidegrees] -->|÷10| T[temperature field]
        P3[Battery Level %] --> L[load_percentage field]
        P4[CPU Usage %] -->|map 0-100% → 10-20A| C[current field]
        P5[Charging State] -->|AC=1.5 USB=3.0 Off=5.5| H[harmonic_5th field]
    end

    subgraph ARDUINO [Arduino/ESP32 via USB Serial]
        A1[Voltage sensor] --> V2[voltage field]
        A2[Current sensor] --> C2[current field]
        A3[Temperature sensor] --> T2[temperature field]
        A4[Harmonic analyzer] --> H2[harmonic_5th field]
        A5[Load meter] --> L2[load_percentage field]
    end

    subgraph SIM [Simulation Mode]
        S1[Gaussian noise\n+ sinusoidal drift] --> ALL[All 5 fields\nrealistic ranges]
    end
```

### Normal Operating Ranges

| Metric | Healthy Range | Warning | Critical |
|---|---|---|---|
| Voltage | 220–240 V | < 210V or > 245V | < 200V or > 250V |
| Current | 10–20 A | > 18A | > 22A |
| Temperature | 50–75 °C | > 75°C | > 85°C |
| Harmonics | 1–5 % | > 5% | > 8% |
| Load | 20–60 % | > 60% | > 80% |

---

## 5. Communication Protocol

```mermaid
sequenceDiagram
    participant SUB as Substation Client
    participant SRV as AI Server (port 9999)
    participant API as FastAPI (port 8000)
    participant DASH as React Dashboard

    SUB->>SRV: TCP Connect
    SRV-->>SUB: Connection accepted

    loop Every 1.5 seconds
        SUB->>SRV: JSON packet + newline
        Note over SRV: Full AI pipeline runs
        SRV-->>SRV: Update health_data, fault_reports, predictions
    end

    loop Every 1.5 seconds
        DASH->>API: GET /state
        API-->>DASH: telemetry + health + load + alerts + predictions
        DASH-->>DASH: Update all charts and cards
    end

    Note over SUB,SRV: On disconnect: state cleaned up automatically
```

### Packet Format

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

Fields may be `null` — the AI pipeline handles partial sensor data gracefully.

---

## 6. AI Pipeline

Every telemetry packet triggers this full pipeline in under 50ms:

```mermaid
flowchart TD
    PKT[Telemetry Packet\nvoltage, current, temp, harmonic, load] --> V

    V[Validate Fields\nshared/utils.py] -->|valid| STORE
    V -->|invalid| DROP[Drop packet]

    STORE[Store in TelemetryManager\nrolling 20-packet history] --> FE

    FE[Feature Engineering\nfeature_pipeline.py\n42 features total] --> IF

    subgraph FEATURES [42 Features Extracted]
        F1[Statistical x30\nmean, std, min, max, range, roc\nper 5 metrics]
        F2[Harmonic x3\nTHD, power factor, severity]
        F3[Phase Unbalance x2\nNEMA %, instability]
        F4[FFT x2\ndominant freq, spectral entropy]
    end

    FE -.-> FEATURES

    IF[IsolationForest\nml_models/isolation_forest.py\nPoint anomaly] --> LSTM

    LSTM[LSTM Detector\nml_models/lstm_anomaly_detector.py\nSequence anomaly\nrequires 10 readings] --> COMBINE

    COMBINE{Either model\nflags anomaly?} -->|Yes| ANOMALY[is_anomaly = True]
    COMBINE -->|No| NORMAL[is_anomaly = False]

    ANOMALY --> SCORE
    NORMAL --> SCORE

    SCORE[Health Score\nml/health_score.py\n100 minus penalties] --> FAULT

    FAULT[Fault Isolation\nsmart_grid/fault_isolation.py\n6 rule-based fault types] --> PRED

    PRED[Overload Predictor\nRandomForest\nrequires 10 readings] --> FAIL

    FAIL[Failure Predictor\nLogisticRegression\nrequires 20 readings] --> REDIST

    REDIST[RedistributionEngine\nml_models/redistribution_engine.py\nSmooth load transition] --> HEAL

    HEAL[SelfHealingEngine\nsmart_grid/self_healing_engine.py\nBackground thread] --> ALERT

    ALERT[AlertManager\nalerts/alert_manager.py\n30s cooldown] --> DONE[State updated\nAPI serves /state]
```

### Step-by-Step Explanation

**Step 1 — Validate & Store**
Every packet is checked for required fields. Valid packets go into `TelemetryManager` which keeps the latest reading and a 20-packet rolling history per substation.

**Step 2 — Feature Engineering (42 features)**
Raw 5 values are expanded to 42 features:
- 30 statistical features (mean, std, min, max, range, rate-of-change × 5 metrics)
- 3 harmonic features (THD approximation, power factor estimate, severity index)
- 2 phase unbalance features (NEMA unbalance %, voltage instability coefficient)
- 2 FFT features (dominant frequency magnitude, spectral entropy)

**Step 3 — IsolationForest (point anomaly)**
Trained on 500 synthetic normal samples at startup. Saved to disk, reloaded on restart. Phone battery voltage (< 10V) is auto-neutralised to prevent false positives.

**Step 4 — LSTM Detector (sequence anomaly)**
One detector per substation. Looks at the last 10 readings as a sequence. Catches gradual drift that looks normal point-by-point but is anomalous as a trend. Combined with IsolationForest: anomaly if either model flags it.

**Step 5 — Health Score**
Starts at 100, applies rule-based penalties. −30 if ML anomaly detected. Score determines status: Healthy (80–100), Warning (50–79), Critical (0–49).

**Step 6 — Fault Isolation**
Six rule-based fault types: Overheat, Voltage Sag, Voltage Surge, Overload, Harmonic Distortion, Overcurrent. Multiple faults can fire simultaneously.

**Step 7 — Overload Prediction**
RandomForest trained on 1500 synthetic sequences. Predicts overload risk in the next 5 readings. Triggers a WARNING alert if probability > 75%.

**Step 8 — Transformer Failure Prediction**
Logistic Regression trained on 2000 sequences. Predicts 24-hour failure probability from 17 stress features (thermal cycles, voltage sag count, harmonic stress, etc.).

**Step 9 — Load Redistribution**
`RedistributionEngine` detects status changes, calls `LoadOptimizer` for optimal distribution, applies it gradually over 10 seconds (5 steps × 2s) with 15-second cooldown.

**Step 10 — Self-Healing**
Background thread checks every 10 seconds. When health rises above 70, load is restored +5% per cycle until the substation reaches its fair share.

**Step 11 — Alert Dispatch**
CRITICAL alerts trigger Email + Slack + SMS in parallel background threads. 30-second cooldown per substation prevents spam.

---
