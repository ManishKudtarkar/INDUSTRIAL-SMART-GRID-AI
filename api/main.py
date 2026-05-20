"""
FastAPI application — AI Smart Grid backend.

Starts the TCP socket server in a background thread and exposes 25 REST endpoints.
Uses lifespan context for clean startup/shutdown.
"""
import threading
import sys
import os
import logging
from contextlib import asynccontextmanager

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

logger = logging.getLogger("smartgrid.api")

# ── Globals (set during lifespan startup) ─────────────────────────────────────
grid_server:       SmartGridSocketServer | None = None
grid_service:      SmartGridService | None      = None
prediction_service: PredictionService | None    = None
alert_service:     AlertService | None          = None


# ── Lifespan — clean startup and shutdown ─────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    global grid_server, grid_service, prediction_service, alert_service

    # ── STARTUP ───────────────────────────────────────────────────────────────
    logger.info("Starting Smart Grid AI backend…")

    grid_server = SmartGridSocketServer(host="0.0.0.0", port=9999)
    _server_thread = threading.Thread(target=grid_server.start, daemon=True, name="socket-server")
    _server_thread.start()

    grid_service        = SmartGridService(grid_server)
    prediction_service  = PredictionService(grid_server.anomaly_detector)
    alert_service       = AlertService(grid_server.alert_manager)
    root_cause_engine   = RootCauseEngine()

    # Inject into route modules
    telemetry_routes.set_service(grid_service)
    anomaly_routes.set_services(prediction_service, grid_service)
    load_routes.set_service(grid_service)
    prediction_routes.set_services(prediction_service, root_cause_engine, grid_service)
    usb_routes.set_service(grid_service)

    logger.info("Smart Grid AI backend ready.")
    yield

    # ── SHUTDOWN ──────────────────────────────────────────────────────────────
    logger.info("Shutting down Smart Grid AI backend…")
    if grid_server:
        grid_server.healer.stop()
    logger.info("Shutdown complete.")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Industrial Smart Grid AI",
    description="Distributed AI-powered smart grid monitoring, anomaly detection, and load balancing.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow all origins for demo/submission
# For production deployment, restrict to your actual frontend URL:
#   allow_origins=["http://localhost", "https://yourdomain.com"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register routers ──────────────────────────────────────────────────────────
app.include_router(telemetry_routes.router)
app.include_router(anomaly_routes.router)
app.include_router(load_routes.router)
app.include_router(prediction_routes.router)
app.include_router(usb_routes.router)


# ── Core endpoints ────────────────────────────────────────────────────────────

@app.get("/", tags=["System"])
def health_check():
    return {
        "status":  "ok",
        "service": "Smart Grid AI Backend",
        "version": "1.0.0",
        "substations_connected": len(grid_server.telemetry_data) if grid_server else 0,
    }


@app.get("/state", tags=["System"])
def get_grid_state():
    """Full live grid state — polled by dashboard every 1.5s."""
    if not grid_service:
        return JSONResponse(status_code=503, content={"error": "Service starting up"})
    return JSONResponse(content=grid_service.get_full_state())


@app.get("/alerts", tags=["Alerts"])
def get_alerts(limit: int = 20):
    if not alert_service:
        return {"alerts": []}
    return {"alerts": alert_service.get_all_alerts(limit=limit)}


@app.get("/alerts/{sub_id}", tags=["Alerts"])
def get_alerts_for_substation(sub_id: str):
    if not alert_service:
        return {"alerts": []}
    return {"substation_id": sub_id, "alerts": alert_service.get_alerts_for_substation(sub_id)}


@app.delete("/alerts", tags=["Alerts"])
def clear_alerts():
    if not alert_service:
        return {"status": "cleared", "count": 0}
    count = alert_service.clear_alerts()
    return {"status": "cleared", "count": count}


@app.get("/summary", tags=["System"])
def get_system_summary():
    if not grid_service:
        return {"status": "starting"}
    return grid_service.get_system_health_summary()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )
