"""
DatabaseManager — optional persistence layer.

Writes telemetry, health scores, alerts, and load snapshots to PostgreSQL.
If the database is not configured (DB_URL not set), all writes are silently
skipped so the system works without a database.

Set DB_URL in your .env:
  DB_URL=postgresql://user:password@localhost:5432/smartgrid
"""
import os
import threading
from typing import Dict, Any, List

from shared.utils import get_logger

logger = get_logger(__name__)

_DB_URL = os.getenv("DB_URL", "")


class DatabaseManager:
    def __init__(self, db_url: str = _DB_URL):
        self._url = db_url
        self._engine = None
        self._lock = threading.Lock()
        self._available = False

        if db_url:
            self._init_engine(db_url)

    # ── Init ──────────────────────────────────────────────────────────────────

    def _init_engine(self, url: str) -> None:
        try:
            from sqlalchemy import create_engine, text
            self._engine = create_engine(url, pool_pre_ping=True, pool_size=5)
            # Test connection
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            self._available = True
            logger.info("Database connection established.")
        except ImportError:
            logger.warning("sqlalchemy not installed — database persistence disabled.")
        except Exception as e:
            logger.warning(f"Database unavailable: {e} — running without persistence.")

    # ── Write ─────────────────────────────────────────────────────────────────

    def save_telemetry(self, packet: Dict[str, Any]) -> None:
        if not self._available:
            return
        sql = """
            INSERT INTO telemetry
                (substation_id, recorded_at, voltage, current, temperature,
                 harmonic_5th, load_percentage, fault_type)
            VALUES
                (:substation_id, :timestamp, :voltage, :current, :temperature,
                 :harmonic_5th, :load_percentage, :fault_type)
        """
        self._execute(sql, {
            "substation_id":  packet.get("substation_id"),
            "timestamp":      packet.get("timestamp"),
            "voltage":        packet.get("voltage"),
            "current":        packet.get("current"),
            "temperature":    packet.get("temperature"),
            "harmonic_5th":   packet.get("harmonic_5th"),
            "load_percentage": packet.get("load_percentage"),
            "fault_type":     packet.get("fault_type"),
        })

    def save_health_score(self, sub_id: str, record: Dict[str, Any]) -> None:
        if not self._available:
            return
        sql = """
            INSERT INTO health_scores
                (substation_id, recorded_at, health_score, risk_level, anomaly_detected)
            VALUES
                (:substation_id, :timestamp, :health_score, :risk_level, :anomaly_detected)
        """
        self._execute(sql, {
            "substation_id":  sub_id,
            "timestamp":      record.get("timestamp"),
            "health_score":   record.get("health_score"),
            "risk_level":     record.get("risk_level"),
            "anomaly_detected": record.get("anomaly_detected", False),
        })

    def save_alert(self, alert: Dict[str, Any]) -> None:
        if not self._available:
            return
        sql = """
            INSERT INTO alerts (substation_id, triggered_at, level, message)
            VALUES (:substation_id, :timestamp, :level, :message)
        """
        self._execute(sql, {
            "substation_id": alert.get("substation_id"),
            "timestamp":     alert.get("timestamp"),
            "level":         alert.get("level"),
            "message":       alert.get("message"),
        })

    def save_load_snapshot(self, distribution: Dict[str, float]) -> None:
        if not self._available:
            return
        from datetime import datetime
        now = datetime.now().isoformat()
        for sub_id, load in distribution.items():
            sql = """
                INSERT INTO load_snapshots (recorded_at, substation_id, load_percentage)
                VALUES (:recorded_at, :substation_id, :load_percentage)
            """
            self._execute(sql, {
                "recorded_at":    now,
                "substation_id":  sub_id,
                "load_percentage": load,
            })

    # ── Private ───────────────────────────────────────────────────────────────

    def _execute(self, sql: str, params: dict) -> None:
        try:
            from sqlalchemy import text
            with self._lock:
                with self._engine.connect() as conn:
                    conn.execute(text(sql), params)
                    conn.commit()
        except Exception as e:
            logger.error(f"DB write failed: {e}")
