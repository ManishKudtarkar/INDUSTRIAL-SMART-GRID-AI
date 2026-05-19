"""
AnomalyDetector — IsolationForest trained on normal operating ranges.

Handles real USB sensor data where some fields may be None.
Missing fields are substituted with the midpoint of their normal range
so the model can still run — but the result is flagged as partial.
"""
import numpy as np
from sklearn.ensemble import IsolationForest
import random

from shared.config import (
    VOLTAGE_MIN, VOLTAGE_MAX,
    CURRENT_MIN, CURRENT_MAX,
    TEMP_MIN, TEMP_MAX,
    HARMONIC_MIN, HARMONIC_MAX,
    LOAD_MIN, LOAD_MAX,
    ISOLATION_FOREST_CONTAMINATION,
    ISOLATION_FOREST_TRAINING_SAMPLES,
)
from shared.utils import get_logger

logger = get_logger(__name__)

# Midpoints used when a sensor field is absent
_FIELD_DEFAULTS = {
    "voltage":         (VOLTAGE_MIN  + VOLTAGE_MAX)  / 2,
    "current":         (CURRENT_MIN  + CURRENT_MAX)  / 2,
    "temperature":     (TEMP_MIN     + TEMP_MAX)     / 2,
    "harmonic_5th":    (HARMONIC_MIN + HARMONIC_MAX) / 2,
    "load_percentage": (LOAD_MIN     + LOAD_MAX)     / 2,
}

FEATURE_ORDER = ["voltage", "current", "temperature", "harmonic_5th", "load_percentage"]


class AnomalyDetector:
    def __init__(self):
        self.model = IsolationForest(
            contamination=ISOLATION_FOREST_CONTAMINATION,
            random_state=42,
        )
        self.is_trained = False
        self._train_initial_model()

    def _train_initial_model(self) -> None:
        """Train on synthetic normal data at startup."""
        logger.info("[ML] Training Anomaly Detector on baseline normal data…")
        normal_data = []
        for _ in range(ISOLATION_FOREST_TRAINING_SAMPLES):
            normal_data.append([
                random.uniform(VOLTAGE_MIN,  VOLTAGE_MAX),
                random.uniform(CURRENT_MIN,  CURRENT_MAX),
                random.uniform(TEMP_MIN,     TEMP_MAX),
                random.uniform(HARMONIC_MIN, HARMONIC_MAX),
                random.uniform(LOAD_MIN,     LOAD_MAX),
            ])
        self.model.fit(normal_data)
        self.is_trained = True
        logger.info("[ML] Anomaly Detector ready.")

    def detect(self, telemetry: dict) -> bool:
        """
        Returns True if anomaly detected, False otherwise.

        If any field is None (sensor didn't send it), the normal-range
        midpoint is substituted so the model can still run.
        Fields that are substituted are logged as a warning.
        """
        features = []
        substituted = []

        for field in FEATURE_ORDER:
            val = telemetry.get(field)
            if val is None:
                features.append(_FIELD_DEFAULTS[field])
                substituted.append(field)
            elif field == "voltage" and float(val) < 10.0:
                # Raw phone battery voltage — substitute neutral grid value
                # so the anomaly detector doesn't false-positive on 3.8V
                features.append(_FIELD_DEFAULTS["voltage"])
                substituted.append(f"voltage(phone_raw={val}→neutral)")
            else:
                features.append(float(val))

        if substituted:
            logger.debug(
                f"[ML] Fields substituted with defaults (not from sensor): {substituted}"
            )

        prediction = self.model.predict(np.array([features]))[0]
        return bool(prediction == -1)   # cast numpy.bool_ → Python bool for JSON
