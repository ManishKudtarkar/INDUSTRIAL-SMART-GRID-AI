"""Pydantic schemas for fault and anomaly data."""
from pydantic import BaseModel
from typing import List, Optional


class FaultDetail(BaseModel):
    name:        str
    severity:    str
    description: str


class FaultReport(BaseModel):
    substation_id:    str
    faults_detected:  List[FaultDetail]
    fault_count:      int
    highest_severity: str


class AnomalyResult(BaseModel):
    substation_id:    str
    anomaly_detected: bool
    health_score:     float
    risk_level:       str
    timestamp:        str
    fault_report:     Optional[FaultReport] = None
