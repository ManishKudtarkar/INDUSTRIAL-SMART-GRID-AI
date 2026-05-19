"""
PredictionService — wraps the ML anomaly detector and health scorer
for use by API route handlers.
"""
from typing import Dict, Any

from ml.anomaly_detector import AnomalyDetector
from ml.health_score import calculate_health_score
from shared.utils import get_logger

logger = get_logger(__name__)


class PredictionService:
    def __init__(self, anomaly_detector: AnomalyDetector):
        self._detector = anomaly_detector

    def predict(self, packet: dict) -> Dict[str, Any]:
        """
        Run anomaly detection + health scoring on a single telemetry packet.

        Returns:
            {
                "substation_id": str,
                "anomaly_detected": bool,
                "health_score": float,
                "risk_level": str,
                "anomaly_score": float   # raw IF decision function value
            }
        """
        import numpy as np

        sub_id = packet.get("substation_id", "Unknown")

        is_anomaly = self._detector.detect(packet)
        score, status = calculate_health_score(packet, is_anomaly)

        # Raw anomaly score (more negative = more anomalous)
        features = np.array([[
            packet["voltage"],
            packet["current"],
            packet["temperature"],
            packet["harmonic_5th"],
            packet["load_percentage"],
        ]])
        raw_score = float(self._detector.model.decision_function(features)[0])

        return {
            "substation_id":    sub_id,
            "anomaly_detected": bool(is_anomaly),
            "health_score":     float(score),
            "risk_level":       status,
            "anomaly_score":    round(float(raw_score), 4),
        }

    def batch_predict(self, packets: list) -> list:
        """Run predict() on a list of packets."""
        return [self.predict(p) for p in packets]
