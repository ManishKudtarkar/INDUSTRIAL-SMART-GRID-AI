"""Telemetry API routes."""
from fastapi import APIRouter, HTTPException
from typing import Optional

router = APIRouter(prefix="/telemetry", tags=["Telemetry"])

# grid_service is injected at app startup (set by main.py)
_grid_service = None

def set_service(service):
    global _grid_service
    _grid_service = service


@router.get("/")
def get_all_telemetry():
    """Return latest telemetry for all connected substations."""
    if _grid_service is None:
        raise HTTPException(status_code=503, detail="Service not initialised")
    return {"telemetry": _grid_service._server.telemetry_data}


@router.get("/{sub_id}")
def get_substation_telemetry(sub_id: str):
    """Return latest telemetry for a specific substation."""
    if _grid_service is None:
        raise HTTPException(status_code=503, detail="Service not initialised")
    detail = _grid_service.get_substation_detail(sub_id)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"Substation {sub_id} not found")
    return {"substation_id": sub_id, "telemetry": detail["telemetry"]}


@router.get("/{sub_id}/history")
def get_telemetry_history(sub_id: str, limit: Optional[int] = 20):
    """Return rolling telemetry history for a substation."""
    if _grid_service is None:
        raise HTTPException(status_code=503, detail="Service not initialised")
    server = _grid_service._server
    if hasattr(server, "telemetry_manager"):
        history = server.telemetry_manager.get_history(sub_id)
        return {"substation_id": sub_id, "history": history[-limit:], "count": len(history)}
    raise HTTPException(status_code=404, detail=f"History not available for {sub_id}")
