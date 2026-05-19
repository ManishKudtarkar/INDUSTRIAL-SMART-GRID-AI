"""
SmartGridService — high-level service for grid state queries.
Used by API routes to access the live grid state from the socket server.
"""
from typing import Dict, Any, List

from shared.utils import get_logger

logger = get_logger(__name__)


class SmartGridService:
    def __init__(self, grid_server):
        """
        grid_server: SmartGridSocketServer instance (holds all live state).
        """
        self._server = grid_server

    def get_full_state(self) -> Dict[str, Any]:
        """Return the complete grid state snapshot."""
        return {
            "telemetry":         self._server.telemetry_data,
            "health":            self._server.health_data,
            "load_distribution": self._server.balancer.load_distribution,
            "alerts":            self._server.alert_manager.get_latest_alerts()[:10],
            "fault_reports":     self._server.fault_reports,
            "substation_count":  len(self._server.telemetry_data),
        }

    def get_substation_detail(self, sub_id: str) -> Dict[str, Any] | None:
        """Return detailed state for a single substation."""
        if sub_id not in self._server.telemetry_data:
            return None
        return {
            "telemetry":    self._server.telemetry_data.get(sub_id, {}),
            "health":       self._server.health_data.get(sub_id, {}),
            "load_target":  self._server.balancer.load_distribution.get(sub_id, 33.3),
            "fault_report": self._server.fault_reports.get(sub_id, {}),
        }

    def get_load_distribution(self) -> Dict[str, float]:
        return dict(self._server.balancer.load_distribution)

    def get_active_substations(self) -> List[str]:
        return list(self._server.telemetry_data.keys())

    def get_system_health_summary(self) -> Dict[str, Any]:
        health = self._server.health_data
        if not health:
            return {"status": "No substations connected", "avg_health": 0}

        scores = [v.get("health_score", 0) for v in health.values()]
        avg = sum(scores) / len(scores)
        critical_count = sum(1 for v in health.values() if v.get("risk_level") == "Critical")
        warning_count  = sum(1 for v in health.values() if v.get("risk_level") == "Warning")

        if critical_count > 0:
            overall = "CRITICAL"
        elif warning_count > 0:
            overall = "WARNING"
        else:
            overall = "HEALTHY"

        return {
            "overall_status":  overall,
            "avg_health_score": round(avg, 1),
            "critical_count":  critical_count,
            "warning_count":   warning_count,
            "healthy_count":   len(health) - critical_count - warning_count,
            "total_substations": len(health),
        }
