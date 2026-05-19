"""
SmartGridSocketServer — TCP server that receives telemetry from all substations,
runs the full AI pipeline, and maintains live grid state.

Pipeline per packet:
  1. Validate & store telemetry
  2. Feature engineering
  3. Anomaly detection (IsolationForest)
  4. Health score calculation
  5. Fault isolation
  6. Alert generation (with cooldown)
  7. Load redistribution
  8. Self-healing notification
"""
import socket
import threading
import json
import sys
import os
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.anomaly_detector import AnomalyDetector
from ml.health_score import calculate_health_score
from smart_grid.load_balancer import LoadBalancer
from smart_grid.fault_isolation import isolate_faults
from smart_grid.self_healing_engine import SelfHealingEngine
from alerts.alert_manager import AlertManager
from server.connection_handler import ConnectionHandler
from server.telemetry_manager import TelemetryManager
from shared.utils import get_logger, validate_telemetry
from shared.config import SERVER_HOST, SERVER_PORT, ALERT_COOLDOWN_SEC

logger = get_logger(__name__)


class SmartGridSocketServer:
    def __init__(self, host: str = SERVER_HOST, port: int = SERVER_PORT):
        self.host = host
        self.port = port

        # ── State stores ──────────────────────────────────────────────────────
        self.telemetry_data: dict = {}      # sub_id → latest packet
        self.health_data:    dict = {}      # sub_id → health record
        self.fault_reports:  dict = {}      # sub_id → fault isolation report

        # ── Components ────────────────────────────────────────────────────────
        self.telemetry_manager = TelemetryManager()
        self.anomaly_detector  = AnomalyDetector()
        self.balancer          = LoadBalancer()
        self.alert_manager     = AlertManager()
        self.healer            = SelfHealingEngine(self.balancer)

        # Alert cooldown tracking: sub_id → last alert datetime
        self._last_alert: dict = {}
        self._lock = threading.Lock()

        # Socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # ── Public ────────────────────────────────────────────────────────────────

    def start(self) -> None:
        self._server_socket.bind((self.host, self.port))
        self._server_socket.listen(10)
        self.healer.start()
        logger.info(f"[SERVER] Listening on {self.host}:{self.port}")

        try:
            while True:
                conn, addr = self._server_socket.accept()
                handler = ConnectionHandler(
                    conn=conn,
                    addr=addr,
                    process_callback=self.process_telemetry,
                    disconnect_callback=self._on_disconnect,
                )
                t = threading.Thread(target=handler.handle, daemon=True)
                t.start()
                logger.info(f"[CONNECTIONS] Active: {threading.active_count() - 1}")
        except KeyboardInterrupt:
            logger.info("Server shutting down.")
        finally:
            self._server_socket.close()

    def process_telemetry(self, packet: dict) -> None:
        """Full AI pipeline for one telemetry packet."""
        sub_id = packet.get("substation_id")
        if not sub_id:
            return

        # 1. Store
        with self._lock:
            self.telemetry_data[sub_id] = packet
        self.telemetry_manager.update(packet)

        # 2. Anomaly detection
        is_anomaly = self.anomaly_detector.detect(packet)

        # 3. Health score
        score, status = calculate_health_score(packet, is_anomaly)

        previous_status = self.health_data.get(sub_id, {}).get("risk_level")

        health_record = {
            "anomaly_detected": bool(is_anomaly),
            "health_score":     float(score),
            "risk_level":       status,
            "timestamp":        packet.get("timestamp", datetime.now().isoformat()),
        }
        with self._lock:
            self.health_data[sub_id] = health_record

        # 4. Fault isolation
        fault_report = isolate_faults(packet)
        with self._lock:
            self.fault_reports[sub_id] = fault_report

        # 5. Alerts (with cooldown to avoid spam)
        self._maybe_alert(sub_id, status, score, previous_status, fault_report)

        # 6. Load redistribution
        active_subs = list(self.telemetry_data.keys())
        self.balancer.redistribute(active_subs, self.health_data)

        # 7. Self-healing notification
        self.healer.notify_health(sub_id, score, status)

        logger.info(
            f"[{sub_id}] V={packet['voltage']}V T={packet['temperature']}°C "
            f"Load={packet['load_percentage']}% Score={score} ({status})"
            + (f" ⚠ ANOMALY" if is_anomaly else "")
        )

    # ── Private ───────────────────────────────────────────────────────────────

    def _maybe_alert(
        self,
        sub_id: str,
        status: str,
        score: float,
        previous_status: str | None,
        fault_report: dict,
    ) -> None:
        """Trigger alerts with cooldown to prevent spam."""
        now = datetime.now()
        last = self._last_alert.get(sub_id)
        cooldown_ok = (last is None) or (now - last > timedelta(seconds=ALERT_COOLDOWN_SEC))

        if status == "Critical" and cooldown_ok:
            faults = ", ".join(f["name"] for f in fault_report.get("faults_detected", []))
            msg = f"Critical state. Score: {score}."
            if faults:
                msg += f" Faults: {faults}."
            self.alert_manager.trigger_alert(sub_id, msg, risk_level="CRITICAL")
            self._last_alert[sub_id] = now

        elif status == "Warning" and previous_status == "Healthy" and cooldown_ok:
            self.alert_manager.trigger_alert(
                sub_id,
                f"Health degraded to Warning. Score: {score}.",
                risk_level="WARNING",
            )
            self._last_alert[sub_id] = now

        elif status == "Healthy" and previous_status in ("Critical", "Warning"):
            self.alert_manager.trigger_alert(
                sub_id,
                f"Substation recovered. Score: {score}.",
                risk_level="INFO",
            )

    def _on_disconnect(self, sub_id: str) -> None:
        """Clean up state when a substation disconnects."""
        with self._lock:
            self.telemetry_data.pop(sub_id, None)
            self.health_data.pop(sub_id, None)
            self.fault_reports.pop(sub_id, None)
        self.telemetry_manager.remove(sub_id)
        logger.info(f"[CLEANUP] Removed state for {sub_id}")


if __name__ == "__main__":
    server = SmartGridSocketServer()
    server.start()
