"""Load balancing and redistribution API routes."""
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/load", tags=["Load Balancing"])

_grid_service = None

def set_service(service):
    global _grid_service
    _grid_service = service


@router.get("/distribution")
def get_load_distribution():
    """Return current load distribution across all substations."""
    if _grid_service is None:
        raise HTTPException(status_code=503, detail="Service not initialised")
    return {
        "load_distribution": _grid_service.get_load_distribution(),
        "total": sum(_grid_service.get_load_distribution().values()),
    }


@router.get("/substations")
def get_active_substations():
    """Return list of currently connected substations."""
    if _grid_service is None:
        raise HTTPException(status_code=503, detail="Service not initialised")
    return {"active_substations": _grid_service.get_active_substations()}


@router.post("/rebalance")
def trigger_rebalance():
    """Manually trigger a load rebalance calculation."""
    if _grid_service is None:
        raise HTTPException(status_code=503, detail="Service not initialised")
    server = _grid_service._server
    active = list(server.telemetry_data.keys())
    new_dist = server.balancer.redistribute(active, server.health_data)
    return {
        "status": "rebalanced",
        "new_distribution": new_dist,
    }
