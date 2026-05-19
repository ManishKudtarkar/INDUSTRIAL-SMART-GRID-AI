"""
Statistical features extracted from a rolling history window.

Features computed per metric (voltage, current, temperature, harmonic_5th, load_percentage):
  mean, std, min, max, range, rate_of_change (last delta)
"""
import statistics
from typing import List, Dict


METRICS = ["voltage", "current", "temperature", "harmonic_5th", "load_percentage"]


def extract_statistical_features(history: List[dict]) -> Dict[str, float]:
    """
    history: list of telemetry dicts, oldest first.
    Returns flat dict of statistical features.
    """
    features: Dict[str, float] = {}

    for metric in METRICS:
        values = [float(p[metric]) for p in history if metric in p]
        if not values:
            continue

        features[f"{metric}_mean"]  = statistics.mean(values)
        features[f"{metric}_std"]   = statistics.pstdev(values) if len(values) > 1 else 0.0
        features[f"{metric}_min"]   = min(values)
        features[f"{metric}_max"]   = max(values)
        features[f"{metric}_range"] = max(values) - min(values)

        # Rate of change: difference between last two readings
        if len(values) >= 2:
            features[f"{metric}_roc"] = values[-1] - values[-2]
        else:
            features[f"{metric}_roc"] = 0.0

    return features
