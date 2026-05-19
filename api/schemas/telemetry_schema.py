"""Pydantic schemas for telemetry-related API endpoints."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class TelemetryPacket(BaseModel):
    substation_id:   str
    timestamp:       datetime
    voltage:         float = Field(..., ge=0, le=500,  description="Voltage in Volts")
    current:         float = Field(..., ge=0, le=100,  description="Current in Amperes")
    temperature:     float = Field(..., ge=-20, le=200, description="Temperature in °C")
    harmonic_5th:    float = Field(..., ge=0, le=50,   description="5th harmonic distortion %")
    load_percentage: float = Field(..., ge=0, le=100,  description="Load as % of rated capacity")
    fault_type:      Optional[str] = None


class TelemetryHistory(BaseModel):
    substation_id: str
    packets:       list[TelemetryPacket]
    count:         int
