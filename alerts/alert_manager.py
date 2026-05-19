"""
AlertManager — thread-safe in-memory alert store with multi-channel dispatch.

Alert levels: CRITICAL, WARNING, INFO
"""
import threading
from datetime import datetime
from typing import List, Dict, Any

from shared.config import MAX_ALERT_HISTORY
from shared.utils import get_logger

logger = get_logger(__name__)


class AlertManager:
    def __init__(self):
        self.active_alerts: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

    # ── Write ─────────────────────────────────────────────────────────────────

    def trigger_alert(
        self,
        substation_id: str,
        message: str,
        risk_level: str = "CRITICAL",
    ) -> Dict[str, Any]:
        """
        Create and store an alert.  Also dispatches to notification channels
        if they are configured (email/Slack/SMS).
        """
        alert = {
            "timestamp":      datetime.now().isoformat(),
            "substation_id":  substation_id,
            "message":        message,
            "level":          risk_level,
        }

        with self._lock:
            self.active_alerts.append(alert)
            if len(self.active_alerts) > MAX_ALERT_HISTORY:
                self.active_alerts.pop(0)

        # Console log
        icons = {"CRITICAL": "🚨", "WARNING": "⚠️", "INFO": "ℹ️"}
        icon = icons.get(risk_level, "🔔")
        logger.warning(f"{icon} [{risk_level}] {substation_id}: {message}")

        # Async notification dispatch (fire-and-forget, won't block the pipeline)
        if risk_level == "CRITICAL":
            self._dispatch_notifications(substation_id, message, risk_level)

        return alert

    # ── Read ──────────────────────────────────────────────────────────────────

    def get_latest_alerts(self, limit: int = MAX_ALERT_HISTORY) -> List[Dict[str, Any]]:
        with self._lock:
            return sorted(
                self.active_alerts,
                key=lambda x: x["timestamp"],
                reverse=True,
            )[:limit]

    def get_by_level(self, level: str) -> List[Dict[str, Any]]:
        with self._lock:
            return [a for a in self.active_alerts if a["level"] == level]

    def count(self) -> Dict[str, int]:
        with self._lock:
            return {
                "total":    len(self.active_alerts),
                "critical": sum(1 for a in self.active_alerts if a["level"] == "CRITICAL"),
                "warning":  sum(1 for a in self.active_alerts if a["level"] == "WARNING"),
                "info":     sum(1 for a in self.active_alerts if a["level"] == "INFO"),
            }

    # ── Private ───────────────────────────────────────────────────────────────

    def _dispatch_notifications(self, sub_id: str, message: str, level: str) -> None:
        """Fire-and-forget notification dispatch in a background thread."""
        import threading

        def _send():
            try:
                from alerts.slack_alert import send_slack_alert
                send_slack_alert(f"Substation {sub_id}: {message}", level=level)
            except Exception:
                pass
            try:
                from alerts.email_alert import send_email_alert
                send_email_alert(
                    subject=f"[{level}] Substation {sub_id}",
                    body=f"Substation: {sub_id}\nLevel: {level}\nMessage: {message}\nTime: {datetime.now().isoformat()}",
                )
            except Exception:
                pass

        threading.Thread(target=_send, daemon=True).start()
