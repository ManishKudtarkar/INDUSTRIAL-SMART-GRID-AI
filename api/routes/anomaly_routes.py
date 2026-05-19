"""Anomaly detection and health score API routes."""
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/anomaly", tags=["Anomaly Detection"])

_prediction_service = None
_grid_service = None

def set_services(prediction_svc, grid_svc):
    global _prediction_service, _grid_service
    _prediction_service = prediction_svc
    _grid_service = grid_svc


@router.get("/health")
def get_all_health():
    """Return health scores for all substations."""
    if _grid_service is None:
        raise HTTPException(status_code=503, detail="Service not initialised")
    return {"health": _grid_service._server.health_data}


@router.get("/health/{sub_id}")
def get_substation_health(sub_id: str):
    """Return health score and anomaly status for a specific substation."""
    if _grid_service is None:
        raise HTTPException(status_code=503, detail="Service not initialised")
    health = _grid_service._server.health_data.get(sub_id)
    if health is None:
        raise HTTPException(status_code=404, detail=f"Substation {sub_id} not found")
    return {"substation_id": sub_id, **health}


@router.get("/summary")
def get_system_health_summary():
    """Return overall system health summary."""
    if _grid_service is None:
        raise HTTPException(status_code=503, detail="Service not initialised")
    return _grid_service.get_system_health_summary()


@router.get("/faults")
def get_all_fault_reports():
    """Return fault isolation reports for all substations."""
    if _grid_service is None:
        raise HTTPException(status_code=503, detail="Service not initialised")
    return {"fault_reports": _grid_service._server.fault_reports}


@router.get("/faults/{sub_id}")
def get_substation_fault_report(sub_id: str):
    """Return fault isolation report for a specific substation."""
    if _grid_service is None:
        raise HTTPException(status_code=503, detail="Service not initialised")
    report = _grid_service._server.fault_reports.get(sub_id)
    if report is None:
        raise HTTPException(status_code=404, detail=f"No fault report for {sub_id}")
    return {"substation_id": sub_id, "fault_report": report}
