"""Prediction and explainability API routes."""
from fastapi import APIRouter, HTTPException, Body

router = APIRouter(prefix="/predict", tags=["Prediction"])

_prediction_service = None
_root_cause_engine  = None

def set_services(prediction_svc, rce):
    global _prediction_service, _root_cause_engine
    _prediction_service = prediction_svc
    _root_cause_engine  = rce


@router.post("/anomaly")
def predict_anomaly(packet: dict = Body(...)):
    """
    Run anomaly detection on a submitted telemetry packet.
    Useful for testing or batch inference.
    """
    if _prediction_service is None:
        raise HTTPException(status_code=503, detail="Service not initialised")
    required = ["voltage", "current", "temperature", "harmonic_5th", "load_percentage"]
    for field in required:
        if field not in packet:
            raise HTTPException(status_code=422, detail=f"Missing field: {field}")
    return _prediction_service.predict(packet)


@router.post("/root-cause")
def get_root_cause(packet: dict = Body(...)):
    """
    Run root cause analysis on a submitted telemetry packet.
    """
    if _root_cause_engine is None:
        raise HTTPException(status_code=503, detail="Root cause engine not initialised")
    health_record = {"anomaly_detected": True, "health_score": 30}
    return _root_cause_engine.analyse(packet, health_record)


@router.get("/model-info")
def get_model_info():
    """Return information about the active ML model."""
    if _prediction_service is None:
        raise HTTPException(status_code=503, detail="Service not initialised")
    detector = _prediction_service._detector
    return {
        "model_type":    type(detector.model).__name__,
        "is_trained":    detector.is_trained,
        "contamination": detector.model.contamination,
        "features":      ["voltage", "current", "temperature", "harmonic_5th", "load_percentage"],
    }
