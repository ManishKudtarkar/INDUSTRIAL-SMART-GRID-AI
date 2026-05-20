"""
Prediction and explainability API routes.

Endpoints:
  POST /predict/anomaly          — point anomaly detection on a packet
  POST /predict/root-cause       — root cause analysis on a packet
  GET  /predict/model-info       — info on all active ML models
  GET  /predict/overload/{sub}   — overload risk for a substation
  GET  /predict/failure/{sub}    — transformer failure risk for a substation
  GET  /predict/all/{sub}        — all predictions for a substation
  POST /predict/optimize-load    — optimal load distribution recommendation
"""
from fastapi import APIRouter, HTTPException, Body

router = APIRouter(prefix="/predict", tags=["Prediction"])

_prediction_service = None
_root_cause_engine  = None
_grid_service       = None

def set_services(prediction_svc, rce, grid_svc=None):
    global _prediction_service, _root_cause_engine, _grid_service
    _prediction_service = prediction_svc
    _root_cause_engine  = rce
    _grid_service       = grid_svc


# ── Anomaly detection ─────────────────────────────────────────────────────────

@router.post("/anomaly")
def predict_anomaly(packet: dict = Body(...)):
    """Run anomaly detection on a submitted telemetry packet."""
    if _prediction_service is None:
        raise HTTPException(status_code=503, detail="Service not initialised")
    required = ["voltage", "current", "temperature", "harmonic_5th", "load_percentage"]
    for field in required:
        if field not in packet:
            raise HTTPException(status_code=422, detail=f"Missing field: {field}")
    return _prediction_service.predict(packet)


# ── Root cause analysis ───────────────────────────────────────────────────────

@router.post("/root-cause")
def get_root_cause(packet: dict = Body(...)):
    """Run root cause analysis on a submitted telemetry packet."""
    if _root_cause_engine is None:
        raise HTTPException(status_code=503, detail="Root cause engine not initialised")
    health_record = {"anomaly_detected": True, "health_score": 30}
    return _root_cause_engine.analyse(packet, health_record)


# ── Model info ────────────────────────────────────────────────────────────────

@router.get("/model-info")
def get_model_info():
    """Return information about all active ML models."""
    if _prediction_service is None:
        raise HTTPException(status_code=503, detail="Service not initialised")
    return _prediction_service.get_model_info()


# ── Overload prediction ───────────────────────────────────────────────────────

@router.get("/overload/{sub_id}")
def predict_overload(sub_id: str):
    """
    Predict overload risk for a substation based on its recent history.
    Requires at least 10 readings in history.
    """
    if _prediction_service is None:
        raise HTTPException(status_code=503, detail="Service not initialised")
    if _grid_service is None:
        raise HTTPException(status_code=503, detail="Grid service not initialised")

    server = _grid_service._server
    if not hasattr(server, "telemetry_manager"):
        raise HTTPException(status_code=503, detail="Telemetry manager not available")

    history = server.telemetry_manager.get_history(sub_id)
    if not history:
        raise HTTPException(status_code=404, detail=f"No history for substation {sub_id}")

    result = _prediction_service.predict_overload(history)
    return {"substation_id": sub_id, "overload_prediction": result}


# ── Transformer failure prediction ────────────────────────────────────────────

@router.get("/failure/{sub_id}")
def predict_failure(sub_id: str):
    """
    Predict transformer failure probability for a substation.
    Requires at least 20 readings in history.
    """
    if _prediction_service is None:
        raise HTTPException(status_code=503, detail="Service not initialised")
    if _grid_service is None:
        raise HTTPException(status_code=503, detail="Grid service not initialised")

    server = _grid_service._server
    history = server.telemetry_manager.get_history(sub_id)
    if not history:
        raise HTTPException(status_code=404, detail=f"No history for substation {sub_id}")

    result = _prediction_service.predict_failure(history)
    return {"substation_id": sub_id, "failure_prediction": result}


# ── All predictions for a substation ─────────────────────────────────────────

@router.get("/all/{sub_id}")
def get_all_predictions(sub_id: str):
    """Return all live predictions for a substation (from server cache)."""
    if _grid_service is None:
        raise HTTPException(status_code=503, detail="Grid service not initialised")

    server = _grid_service._server
    predictions = getattr(server, "predictions", {})
    sub_preds = predictions.get(sub_id, {})

    return {
        "substation_id": sub_id,
        "predictions":   sub_preds,
        "has_data":      bool(sub_preds),
    }


# ── Load optimization ─────────────────────────────────────────────────────────

@router.post("/optimize-load")
def optimize_load(health_data: dict = Body(...)):
    """
    Get optimal load distribution recommendation.
    Body: {sub_id: {health_score: float, risk_level: str}, ...}
    """
    if _prediction_service is None:
        raise HTTPException(status_code=503, detail="Service not initialised")
    return _prediction_service.optimize_load(health_data)
