"""
MetricsCollector — exposes Prometheus-compatible metrics.

Metrics exposed:
  smartgrid_health_score{substation}     — current health score (gauge)
  smartgrid_anomaly_total{substation}    — cumulative anomaly count (counter)
  smartgrid_load_pct{substation}         — current load percentage (gauge)
  smartgrid_temperature{substation}      — current temperature (gauge)
  smartgrid_voltage{substation}          — current voltage (gauge)
  smartgrid_alerts_total{level}          — cumulative alert count (counter)

If the prometheus_client package is not installed, metrics are silently
skipped and the system continues to work normally.
"""
import threading
from typing import Dict, Any

from shared.utils import get_logger

logger = get_logger(__name__)

_prometheus_available = False
_gauges: Dict[str, Any] = {}
_counters: Dict[str, Any] = {}

try:
    from prometheus_client import Gauge, Counter, start_http_server
    _prometheus_available = True
    logger.info("Prometheus client available.")
except ImportError:
    logger.debug("prometheus_client not installed — metrics endpoint disabled.")


def _init_metrics() -> None:
    global _gauges, _counters
    if not _prometheus_available:
        return
    from prometheus_client import Gauge, Counter
    _gauges = {
        "health_score": Gauge("smartgrid_health_score",  "Substation health score",  ["substation"]),
        "load_pct":     Gauge("smartgrid_load_pct",      "Load percentage",           ["substation"]),
        "temperature":  Gauge("smartgrid_temperature",   "Temperature °C",            ["substation"]),
        "voltage":      Gauge("smartgrid_voltage",       "Voltage V",                 ["substation"]),
    }
    _counters = {
        "anomaly":  Counter("smartgrid_anomaly_total",  "Anomaly detections",  ["substation"]),
        "alerts":   Counter("smartgrid_alerts_total",   "Alerts triggered",    ["level"]),
    }


_init_metrics()


class MetricsCollector:
    def __init__(self, port: int = 9090):
        self._port = port
        self._started = False

    def start_server(self) -> None:
        """Start the Prometheus HTTP metrics server on the configured port."""
        if not _prometheus_available:
            logger.info("Prometheus metrics server not started (package unavailable).")
            return
        if self._started:
            return
        try:
            from prometheus_client import start_http_server
            t = threading.Thread(
                target=start_http_server,
                args=(self._port,),
                daemon=True,
            )
            t.start()
            self._started = True
            logger.info(f"Prometheus metrics server started on port {self._port}.")
        except Exception as e:
            logger.error(f"Failed to start Prometheus server: {e}")

    def update(self, sub_id: str, telemetry: dict, health: dict) -> None:
        """Update all gauges for a substation."""
        if not _prometheus_available or not _gauges:
            return
        try:
            _gauges["health_score"].labels(substation=sub_id).set(health.get("health_score", 0))
            _gauges["load_pct"].labels(substation=sub_id).set(telemetry.get("load_percentage", 0))
            _gauges["temperature"].labels(substation=sub_id).set(telemetry.get("temperature", 0))
            _gauges["voltage"].labels(substation=sub_id).set(telemetry.get("voltage", 0))

            if health.get("anomaly_detected"):
                _counters["anomaly"].labels(substation=sub_id).inc()
        except Exception as e:
            logger.debug(f"Metrics update error: {e}")

    def record_alert(self, level: str) -> None:
        """Increment the alert counter for a given level."""
        if not _prometheus_available or not _counters:
            return
        try:
            _counters["alerts"].labels(level=level).inc()
        except Exception as e:
            logger.debug(f"Alert counter error: {e}")
