"""
CriticalShutdown — emergency response actions for extreme fault conditions.

When a substation's health score drops to 0 or a combined fault is detected,
this module can:
  1. Log a critical shutdown event
  2. Notify all channels simultaneously
  3. (In production) send a relay trip command to the substation

This is intentionally conservative — actual relay commands require
hardware integration and are stubbed here.
"""
import threading
from datetime import datetime
from typing import Callable

from alerts.email_alert import send_email_alert
from alerts.slack_alert import send_slack_alert
from alerts.sms_alert   import send_sms_alert
from shared.utils import get_logger

logger = get_logger(__name__)

# Registry of shutdown events (in-memory)
_shutdown_log: list = []
_log_lock = threading.Lock()


def trigger_critical_shutdown(
    sub_id: str,
    reason: str,
    health_score: float,
    on_shutdown: Callable[[str], None] | None = None,
) -> dict:
    """
    Execute emergency shutdown protocol for a substation.

    sub_id       : substation identifier
    reason       : human-readable reason string
    health_score : current health score (expected near 0)
    on_shutdown  : optional callback(sub_id) for hardware relay trip

    Returns the shutdown event record.
    """
    event = {
        "timestamp":    datetime.now().isoformat(),
        "substation_id": sub_id,
        "reason":        reason,
        "health_score":  health_score,
        "actions_taken": [],
    }

    logger.critical(
        f"[CRITICAL SHUTDOWN] {sub_id} | Score: {health_score} | Reason: {reason}"
    )

    # ── Notify all channels in parallel ───────────────────────────────────────
    subject = f"CRITICAL SHUTDOWN — Substation {sub_id}"
    body = (
        f"Emergency shutdown triggered.\n"
        f"Substation : {sub_id}\n"
        f"Health Score: {health_score}\n"
        f"Reason      : {reason}\n"
        f"Timestamp   : {event['timestamp']}\n"
    )

    threads = [
        threading.Thread(target=send_email_alert, args=(subject, body), daemon=True),
        threading.Thread(target=send_slack_alert, args=(body, "CRITICAL"), daemon=True),
        threading.Thread(target=send_sms_alert,   args=(f"{subject}: {reason}",), daemon=True),
    ]
    for t in threads:
        t.start()
    event["actions_taken"].append("notifications_dispatched")

    # ── Hardware relay trip (stub) ─────────────────────────────────────────────
    if on_shutdown:
        try:
            on_shutdown(sub_id)
            event["actions_taken"].append("relay_trip_executed")
            logger.info(f"[SHUTDOWN] Relay trip callback executed for {sub_id}.")
        except Exception as e:
            logger.error(f"[SHUTDOWN] Relay trip callback failed: {e}")

    # ── Log the event ─────────────────────────────────────────────────────────
    with _log_lock:
        _shutdown_log.append(event)
        if len(_shutdown_log) > 200:
            _shutdown_log.pop(0)

    return event


def get_shutdown_log() -> list:
    """Return all recorded shutdown events, newest first."""
    with _log_lock:
        return sorted(_shutdown_log, key=lambda e: e["timestamp"], reverse=True)
