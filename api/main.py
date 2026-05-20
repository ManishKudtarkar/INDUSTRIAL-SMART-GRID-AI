"""
FastAPI application — AI Smart Grid backend.

Starts the TCP socket server in a background thread and exposes:
  GET  /              — health check
  GET  /state         — full grid state snapshot
  GET  /telemetry/*   — telemetry routes
  GET  /anomaly/*     — health & fault routes
  GET  /load/*        — load balancing routes
  POST /predict/*     — on-demand prediction & explainability
  GET  /alerts/*      — alert management routes
"""
import threading
import sys
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.socket_server import SmartGridSocketServer
from api.services.smart_grid_service import SmartGridService
from api.services.prediction_service import PredictionService
from api.services.alert_service import AlertService
from explainability.root_cause_engine import RootCauseEngine

import api.routes.telemetry_routes      as telemetry_routes
import api.routes.anomaly_routes        as anomaly_routes
import api.routes.load_balancing_routes as load_routes
import api.routes.prediction_routes     as prediction_routes
import api.routes.usb_routes            as usb_routes

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Industrial Smart Grid AI",
    description="Distributed AI-powered smart grid monitoring, anomaly detection, and load balancing.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Initialise components ─────────────────────────────────────────────────────

grid_server = SmartGridSocketServer(host="0.0.0.0", port=9999)

# Start socket server in background thread
_server_thread = threading.Thread(target=grid_server.start, daemon=True)
_server_thread.start()

# Services
grid_service       = SmartGridService(grid_server)
prediction_service = PredictionService(grid_server.anomaly_detector)
alert_service      = AlertService(grid_server.alert_manager)
root_cause_engine  = RootCauseEngine()   # SHAP optional

# Inject services into route modules
telemetry_routes.set_service(grid_service)
anomaly_routes.set_services(prediction_service, grid_service)
load_routes.set_service(grid_service)
prediction_routes.set_services(prediction_service, root_cause_engine, grid_service)
usb_routes.set_service(grid_service)

# ── Register routers ──────────────────────────────────────────────────────────

app.include_router(telemetry_routes.router)
app.include_router(anomaly_routes.router)
app.include_router(load_routes.router)
app.include_router(prediction_routes.router)
app.include_router(usb_routes.router)

# ── Core endpoints ────────────────────────────────────────────────────────────

@app.get("/", tags=["System"])
def health_check():
    return {"status": "ok", "service": "Smart Grid AI Backend", "version": "1.0.0"}


@app.get("/state", tags=["System"])
def get_grid_state():
    """
    Primary dashboard endpoint — returns full live grid state.
    Polled by the Streamlit dashboard every 1.5 seconds.
    """
    return JSONResponse(content=grid_service.get_full_state())


@app.get("/alerts", tags=["Alerts"])
def get_alerts(limit: int = 20):
    return {"alerts": alert_service.get_all_alerts(limit=limit)}


@app.get("/alerts/{sub_id}", tags=["Alerts"])
def get_alerts_for_substation(sub_id: str):
    return {"substation_id": sub_id, "alerts": alert_service.get_alerts_for_substation(sub_id)}


@app.delete("/alerts", tags=["Alerts"])
def clear_alerts():
    count = alert_service.clear_alerts()
    return {"status": "cleared", "count": count}


@app.get("/summary", tags=["System"])
def get_system_summary():
    return grid_service.get_system_health_summary()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
