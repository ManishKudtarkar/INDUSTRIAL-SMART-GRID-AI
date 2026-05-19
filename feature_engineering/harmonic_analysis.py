"""
Harmonic analysis features.

In real power systems the 5th harmonic is the dominant distortion component.
We derive additional indicators from the raw harmonic_5th reading.
"""
import math
from typing import Dict


# IEEE 519 limits for industrial systems
THD_WARNING_THRESHOLD  = 5.0   # %
THD_CRITICAL_THRESHOLD = 8.0   # %


def extract_harmonic_features(packet: dict) -> Dict[str, float]:
    """
    Derive harmonic-related features from a single telemetry packet.
    """
    h5 = float(packet.get("harmonic_5th", 0))

    # Approximate Total Harmonic Distortion assuming 5th is dominant
    # THD ≈ h5 (simplified; real THD needs all harmonics)
    thd_approx = h5

    # Harmonic severity index (0 = clean, 1 = at warning, 2 = critical)
    if thd_approx < THD_WARNING_THRESHOLD:
        severity = 0.0
    elif thd_approx < THD_CRITICAL_THRESHOLD:
        severity = 1.0
    else:
        severity = 2.0

    # Power factor degradation estimate (simplified)
    # PF ≈ 1 / sqrt(1 + THD²)
    pf_estimate = 1.0 / math.sqrt(1 + (thd_approx / 100) ** 2)

    return {
        "thd_approx":        round(thd_approx, 3),
        "harmonic_severity": severity,
        "pf_estimate":       round(pf_estimate, 4),
    }
