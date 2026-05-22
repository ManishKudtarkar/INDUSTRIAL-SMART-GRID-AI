# API Documentation

Base URL: `http://localhost:8000`

## System

- `GET /` - backend health check and connected substation count.
- `GET /state` - full dashboard state: telemetry, health, load distribution, alerts, faults, predictions, and redistribution history.
- `GET /summary` - aggregate health summary across connected substations.

## Telemetry

- `GET /telemetry/` - latest telemetry for all substations.
- `GET /telemetry/{sub_id}` - latest telemetry for one substation.
- `GET /telemetry/{sub_id}/history?limit=20` - rolling telemetry history.

## Anomaly And Faults

- `GET /anomaly/health` - health records for all substations.
- `GET /anomaly/health/{sub_id}` - health record for one substation.
- `GET /anomaly/summary` - system health summary.
- `GET /anomaly/faults` - fault reports for all substations.
- `GET /anomaly/faults/{sub_id}` - fault report for one substation.

## Prediction

- `POST /predict/anomaly` - run point anomaly detection on a submitted telemetry packet.
- `POST /predict/root-cause` - run rule-based root cause analysis for a submitted packet.
- `GET /predict/model-info` - active model metadata.
- `GET /predict/overload/{sub_id}` - overload prediction from recent history.
- `GET /predict/failure/{sub_id}` - transformer failure prediction from recent history.
- `GET /predict/all/{sub_id}` - cached live predictions for one substation.
- `POST /predict/optimize-load` - load distribution recommendation from supplied health data.

## Load Balancing

- `GET /load/distribution` - current target load distribution.
- `GET /load/substations` - active substation IDs.
- `POST /load/rebalance` - manually trigger load redistribution.

## Alerts

- `GET /alerts?limit=20` - recent alerts.
- `GET /alerts/{sub_id}` - alerts for one substation.
- `DELETE /alerts` - clear in-memory alerts.

## USB

- `GET /usb/status` - available serial ports plus best-effort active substation mapping.
- `GET /usb/ports` - raw serial port list.
