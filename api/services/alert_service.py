"""
AlertService — business logic layer between the API routes and AlertManager.
"""
from typing import List, Dict, Any

from alerts.alert_manager import AlertManager
from shared.utils import get_logger

logger = get_logger(__name__)


class AlertService:
    def __init__(self, alert_manager: AlertManager):
        self._manager = alert_manager

    def get_all_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self._manager.get_latest_alerts()[:limit]

    def get_alerts_for_substation(self, sub_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        all_alerts = self._manager.get_latest_alerts()
        return [a for a in all_alerts if a["substation_id"] == sub_id][:limit]

    def get_critical_alerts(self) -> List[Dict[str, Any]]:
        return [a for a in self._manager.get_latest_alerts() if a["level"] == "CRITICAL"]

    def clear_alerts(self) -> int:
        count = len(self._manager.active_alerts)
        self._manager.active_alerts.clear()
        logger.info(f"Cleared {count} alerts.")
        return count

    def alert_count(self) -> Dict[str, int]:
        alerts = self._manager.get_latest_alerts()
        return {
            "total":    len(alerts),
            "critical": sum(1 for a in alerts if a["level"] == "CRITICAL"),
            "warning":  sum(1 for a in alerts if a["level"] == "WARNING"),
        }
