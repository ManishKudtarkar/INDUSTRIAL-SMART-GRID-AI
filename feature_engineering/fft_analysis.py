"""
FFT-based features from the voltage time series.

A short FFT over the rolling voltage window gives frequency-domain
indicators that can reveal oscillations or resonance — early signs of
instability that are invisible in the time domain.
"""
import math
from typing import List, Dict


def extract_fft_features(history: List[dict]) -> Dict[str, float]:
    """
    history: list of telemetry dicts (oldest first), minimum 8 entries.
    Returns dominant frequency magnitude and spectral entropy.
    """
    voltages = [float(p["voltage"]) for p in history if "voltage" in p]
    n = len(voltages)
    if n < 8:
        return {}

    # Remove DC component (mean)
    mean_v = sum(voltages) / n
    signal = [v - mean_v for v in voltages]

    # Manual DFT (avoid numpy dependency for portability)
    magnitudes = []
    for k in range(1, n // 2 + 1):
        re = sum(signal[t] * math.cos(2 * math.pi * k * t / n) for t in range(n))
        im = sum(signal[t] * math.sin(2 * math.pi * k * t / n) for t in range(n))
        magnitudes.append(math.sqrt(re ** 2 + im ** 2) / n)

    if not magnitudes:
        return {}

    dominant_magnitude = max(magnitudes)

    # Spectral entropy — low entropy = energy concentrated in few frequencies (bad)
    total = sum(magnitudes) + 1e-9
    probs = [m / total for m in magnitudes]
    spectral_entropy = -sum(p * math.log(p + 1e-9) for p in probs)

    return {
        "fft_dominant_magnitude": round(dominant_magnitude, 4),
        "fft_spectral_entropy":   round(spectral_entropy, 4),
    }
