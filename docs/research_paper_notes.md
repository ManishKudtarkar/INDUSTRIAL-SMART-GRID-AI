# Research Notes

## Scope

This project is a prototype SCADA-style monitoring stack for industrial smart grid telemetry. It combines streaming telemetry, interpretable rules, anomaly detection, predictive maintenance, load redistribution, and operator dashboards.

## Modeling Approach

- Isolation Forest provides fast point anomaly detection with low runtime overhead.
- A sequence model layer catches gradual drift that a point detector can miss.
- Deterministic health scoring keeps operator-facing risk labels explainable.
- Forecasting models estimate overload and transformer failure risk from rolling history.

## Design Tradeoffs

- The default runtime avoids TensorFlow so it can run in lightweight Docker and common Python environments.
- Optional TensorFlow code is kept separate for experimentation.
- In-memory state keeps the dashboard responsive; optional PostgreSQL persistence handles audit/history needs.
- Hardware shutdown is intentionally callback-based because relay protocols vary by device and site.

## Evaluation Ideas

- Replay synthetic and hardware telemetry through the socket server and compare alert timing.
- Measure false positives for phone-derived ADB telemetry versus grid-range voltage telemetry.
- Run load tests with many simulated substations to validate socket concurrency and API latency.
- Compare Isolation Forest-only results with combined point and sequence detection.
