"""Generic API response wrappers."""
from pydantic import BaseModel
from typing import Any, Optional


class SuccessResponse(BaseModel):
    status:  str = "ok"
    data:    Any = None
    message: Optional[str] = None


class ErrorResponse(BaseModel):
    status:  str = "error"
    message: str
    detail:  Optional[str] = None


class GridStateResponse(BaseModel):
    telemetry:         dict
    health:            dict
    load_distribution: dict
    alerts:            list
    fault_reports:     dict
    substation_count:  int
