"""
FeaturePipeline — orchestrates all feature extraction steps.

Takes a raw telemetry packet + history window and returns an enriched
feature dict ready for ML inference or health scoring.
"""
from typing import List, Dict

from feature_engineering.statistical_features import extract_statistical_features
from feature_engineering.harmonic_analysis import extract_harmonic_features
from feature_engineering.phase_unbalance import compute_phase_unbalance
from feature_engineering.fft_analysis import extract_fft_features


class FeaturePipeline:
    def __init__(self):
        pass

    def transform(self, packet: dict, history: List[dict]) -> Dict[str, float]:
        """
        packet  : latest telemetry dict
        history : list of recent telemetry dicts (oldest first)

        Returns a flat dict of engineered features.
        """
        features: Dict[str, float] = {}

        # Raw passthrough
        for key in ("voltage", "current", "temperature", "harmonic_5th", "load_percentage"):
            features[key] = float(packet.get(key, 0))

        # Statistical features from history
        if history:
            features.update(extract_statistical_features(history))

        # Harmonic analysis
        features.update(extract_harmonic_features(packet))

        # Phase unbalance (requires history)
        if len(history) >= 3:
            features.update(compute_phase_unbalance(history))

        # FFT-based features
        if len(history) >= 8:
            features.update(extract_fft_features(history))

        return features
