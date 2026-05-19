"""
Feature importance analysis for the anomaly detection model.

Computes permutation importance — shuffles each feature and measures
how much the anomaly detection rate changes.  Works with any sklearn model.
"""
import numpy as np
import random
from typing import Dict, List

from shared.utils import get_logger

logger = get_logger(__name__)

FEATURE_NAMES = ["voltage", "current", "temperature", "harmonic_5th", "load_percentage"]


def compute_permutation_importance(
    model,
    test_data: List[dict],
    n_repeats: int = 5,
) -> Dict[str, float]:
    """
    Estimate feature importance via permutation on a list of telemetry dicts.

    Returns a dict mapping feature_name → importance_score (higher = more important).
    """
    if not test_data:
        return {f: 0.0 for f in FEATURE_NAMES}

    X = np.array([
        [p["voltage"], p["current"], p["temperature"], p["harmonic_5th"], p["load_percentage"]]
        for p in test_data
    ])

    baseline_preds = model.predict(X)
    baseline_anomaly_rate = float(np.mean(baseline_preds == -1))

    importances: Dict[str, float] = {}

    for i, feature in enumerate(FEATURE_NAMES):
        deltas = []
        for _ in range(n_repeats):
            X_permuted = X.copy()
            np.random.shuffle(X_permuted[:, i])
            preds = model.predict(X_permuted)
            permuted_rate = float(np.mean(preds == -1))
            deltas.append(abs(permuted_rate - baseline_anomaly_rate))
        importances[feature] = round(float(np.mean(deltas)), 4)

    # Normalise to sum to 1
    total = sum(importances.values()) + 1e-9
    importances = {k: round(v / total, 4) for k, v in importances.items()}

    logger.info(f"Feature importances: {importances}")
    return importances


def rank_features(importances: Dict[str, float]) -> List[tuple]:
    """Return features sorted by importance descending."""
    return sorted(importances.items(), key=lambda x: x[1], reverse=True)
