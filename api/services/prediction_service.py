"""
PredictionService — wraps ALL ML models for use by API route handlers.

Models exposed:
  - IsolationForest anomaly detection  (point-based)
  - LSTM sequence anomaly detection    (trend-based)
  - HealthScoreModel                   (ML-based health scoring)
  - OverloadPredictor                  (next-N-readings overload risk)
  - TransformerFailurePredictor        (24-hour failure probability)
"""
import os
import sys
from typing import Dict, Any, List

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from ml.anomaly_detector import AnomalyDetector
from ml.health_score import calculate_health_score
from shared.utils import get_logger

logger = get_logger(__name__)

# ── Optional advanced models ──────────────────────────────────────────────────
try:
    from ml_models.prediction.health_score_model import HealthScoreModel
    _hs_model = HealthScoreModel()
    if not _hs_model.load():
        _hs_model.train()
        _hs_model.save()
    _HEALTH_MODEL_AVAILABLE = True
except Exception as e:
    _hs_model = None
    _HEALTH_MODEL_AVAILABLE = False
    logger.warning(f"HealthScoreModel unavailable: {e}")

try:
    from ml_models.prediction.overload_predictor import OverloadPredictor
    _overload_model = OverloadPredictor()
    if not _overload_model.load():
        _overload_model.train()
        _overload_model.save()
    _OVERLOAD_AVAILABLE = True
except Exception as e:
    _overload_model = None
    _OVERLOAD_AVAILABLE = False
    logger.warning(f"OverloadPredictor unavailable: {e}")

try:
    from ml_models.prediction.transformer_failure_predictor import TransformerFailurePredictor
    _failure_model = TransformerFailurePredictor()
    if not _failure_model.load():
        _failure_model.train()
        _failure_model.save()
    _FAILURE_AVAILABLE = True
except Exception as e:
    _failure_model = None
    _FAILURE_AVAILABLE = False
    logger.warning(f"TransformerFailurePredictor unavailable: {e}")

try:
    from ml_models.load_balancing.load_optimizer import LoadOptimizer
    _load_optimizer = LoadOptimizer()
    _OPTIMIZER_AVAILABLE = True
except Exception as e:
    _load_optimizer = None
    _OPTIMIZER_AVAILABLE = False


class PredictionService:
    def __init__(self, anomaly_detector: AnomalyDetector):
        self._detector = anomaly_detector

    # ── Anomaly detection ─────────────────────────────────────────────────────

    def predict(self, packet: dict) -> Dict[str, Any]:
        """Point-based anomaly detection + health scoring."""
        sub_id = packet.get("substation_id", "Unknown")
        result = self._detector.detect_with_score(packet)
        is_anomaly = result["anomaly"]
        score, status = calculate_health_score(packet, is_anomaly)

        # ML-based health score (if available)
        ml_score = None
        if _HEALTH_MODEL_AVAILABLE:
            try:
                ml_score = _hs_model.predict(packet, is_anomaly)
            except Exception:
                pass

        return {
            "substation_id":    sub_id,
            "anomaly_detected": bool(is_anomaly),
            "anomaly_score":    float(result.get("score", 0.0)),
            "raw_if_score":     float(result.get("raw_score", 0.0)),
            "health_score":     float(score),
            "ml_health_score":  ml_score,
            "risk_level":       status,
        }

    def batch_predict(self, packets: list) -> list:
        return [self.predict(p) for p in packets]

    # ── Overload prediction ───────────────────────────────────────────────────

    def predict_overload(self, history: List[dict]) -> Dict[str, Any]:
        """Predict overload risk from rolling history."""
        if not _OVERLOAD_AVAILABLE:
            return {"error": "OverloadPredictor not available", "available": False}
        return _overload_model.predict(history)

    # ── Transformer failure prediction ────────────────────────────────────────

    def predict_failure(self, history: List[dict]) -> Dict[str, Any]:
        """Predict transformer failure probability from rolling history."""
        if not _FAILURE_AVAILABLE:
            return {"error": "TransformerFailurePredictor not available", "available": False}
        return _failure_model.predict(history)

    # ── Load optimization ─────────────────────────────────────────────────────

    def optimize_load(self, health_data: Dict[str, dict]) -> Dict[str, Any]:
        """Get optimal load distribution recommendation."""
        if not _OPTIMIZER_AVAILABLE:
            return {"error": "LoadOptimizer not available", "available": False}
        return _load_optimizer.get_recommendation(health_data)

    # ── Model info ────────────────────────────────────────────────────────────

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "anomaly_detector": {
                "type":       type(self._detector._detector).__name__ if hasattr(self._detector, "_detector") and self._detector._detector else "IsolationForest",
                "is_trained": self._detector.is_trained,
                "features":   ["voltage", "current", "temperature", "harmonic_5th", "load_percentage"],
            },
            "health_score_model": {
                "available": _HEALTH_MODEL_AVAILABLE,
                "type":      "GradientBoostingRegressor" if _HEALTH_MODEL_AVAILABLE else None,
            },
            "overload_predictor": {
                "available": _OVERLOAD_AVAILABLE,
                "type":      "RandomForestClassifier" if _OVERLOAD_AVAILABLE else None,
                "horizon":   5,
            },
            "transformer_failure_predictor": {
                "available":      _FAILURE_AVAILABLE,
                "type":           "LogisticRegression" if _FAILURE_AVAILABLE else None,
                "horizon_hours":  24,
            },
            "load_optimizer": {
                "available": _OPTIMIZER_AVAILABLE,
                "type":      "WeightedProportionalAllocation" if _OPTIMIZER_AVAILABLE else None,
            },
        }
