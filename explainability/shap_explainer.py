"""
SHAP-based explainability for the Isolation Forest anomaly detector.

Uses TreeExplainer (fast, exact for tree-based models) to compute
feature contributions for each prediction.

Usage:
    explainer = ShapExplainer(anomaly_detector.model)
    explanation = explainer.explain(packet)
"""
import numpy as np
from typing import Dict, Any

from shared.utils import get_logger

logger = get_logger(__name__)

FEATURE_NAMES = ["voltage", "current", "temperature", "harmonic_5th", "load_percentage"]


class ShapExplainer:
    def __init__(self, model):
        """
        model: a fitted sklearn IsolationForest (or any tree ensemble).
        """
        self._model = model
        self._explainer = None
        self._init_explainer()

    def _init_explainer(self) -> None:
        try:
            import shap
            self._explainer = shap.TreeExplainer(self._model)
            logger.info("SHAP TreeExplainer initialised.")
        except ImportError:
            logger.warning("shap package not installed — SHAP explanations disabled.")
        except Exception as e:
            logger.warning(f"SHAP init failed: {e} — explanations disabled.")

    def explain(self, packet: dict) -> Dict[str, Any]:
        """
        Compute SHAP values for a single telemetry packet.

        Returns:
            {
                "feature_contributions": {"voltage": 0.12, ...},
                "top_contributor": "temperature",
                "explanation_text": "...",
                "shap_available": bool
            }
        """
        if self._explainer is None:
            return self._fallback_explanation(packet)

        try:
            import shap
            features = np.array([[
                packet["voltage"],
                packet["current"],
                packet["temperature"],
                packet["harmonic_5th"],
                packet["load_percentage"],
            ]])

            shap_values = self._explainer.shap_values(features)
            # For IsolationForest, shap_values shape is (1, n_features)
            if isinstance(shap_values, list):
                values = shap_values[0][0]
            else:
                values = shap_values[0]

            contributions = {
                name: round(float(val), 4)
                for name, val in zip(FEATURE_NAMES, values)
            }

            # Top contributor (largest absolute SHAP value)
            top = max(contributions, key=lambda k: abs(contributions[k]))

            text = self._build_explanation_text(contributions, top, packet)

            return {
                "feature_contributions": contributions,
                "top_contributor":       top,
                "explanation_text":      text,
                "shap_available":        True,
            }

        except Exception as e:
            logger.error(f"SHAP explain failed: {e}")
            return self._fallback_explanation(packet)

    # ── private ───────────────────────────────────────────────────────────────

    def _fallback_explanation(self, packet: dict) -> Dict[str, Any]:
        """Rule-based fallback when SHAP is unavailable."""
        from shared.config import VOLTAGE_MIN, VOLTAGE_MAX, TEMP_MAX, HARMONIC_MAX, LOAD_MAX

        reasons = []
        if packet.get("temperature", 0) > TEMP_MAX:
            reasons.append(f"temperature={packet['temperature']}°C exceeds {TEMP_MAX}°C")
        if not (VOLTAGE_MIN <= packet.get("voltage", 230) <= VOLTAGE_MAX):
            reasons.append(f"voltage={packet['voltage']}V outside {VOLTAGE_MIN}–{VOLTAGE_MAX}V")
        if packet.get("harmonic_5th", 0) > HARMONIC_MAX:
            reasons.append(f"harmonic_5th={packet['harmonic_5th']}% exceeds {HARMONIC_MAX}%")
        if packet.get("load_percentage", 0) > LOAD_MAX:
            reasons.append(f"load={packet['load_percentage']}% exceeds {LOAD_MAX}%")

        text = "Anomaly likely caused by: " + ("; ".join(reasons) if reasons else "unknown deviation.")
        return {
            "feature_contributions": {},
            "top_contributor":       reasons[0].split("=")[0] if reasons else "unknown",
            "explanation_text":      text,
            "shap_available":        False,
        }

    def _build_explanation_text(self, contributions: dict, top: str, packet: dict) -> str:
        direction = "increased" if contributions[top] > 0 else "decreased"
        value = packet.get(top, "N/A")
        return (
            f"The anomaly score was most influenced by '{top}' (value={value}), "
            f"which {direction} the anomaly likelihood. "
            f"Other contributors: {', '.join(k for k in contributions if k != top)}."
        )
