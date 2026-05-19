"""
Phase unbalance estimation from voltage history.

In a balanced 3-phase system all phase voltages are equal.
We approximate unbalance using the NEMA definition:
  unbalance % = (max deviation from mean / mean) × 100

Since we only have a single voltage reading per packet, we use the
rolling window to estimate voltage variability as a proxy for unbalance.
"""
import statistics
from typing import List, Dict


def compute_phase_unbalance(history: List[dict]) -> Dict[str, float]:
    """
    history: list of recent telemetry dicts.
    Returns phase unbalance estimate and related features.
    """
    voltages = [float(p["voltage"]) for p in history if "voltage" in p]
    if len(voltages) < 3:
        return {"phase_unbalance_pct": 0.0, "voltage_instability": 0.0}

    mean_v = statistics.mean(voltages)
    if mean_v == 0:
        return {"phase_unbalance_pct": 0.0, "voltage_instability": 0.0}

    max_deviation = max(abs(v - mean_v) for v in voltages)
    unbalance_pct = (max_deviation / mean_v) * 100

    # Voltage instability: coefficient of variation
    std_v = statistics.pstdev(voltages)
    cv = (std_v / mean_v) * 100

    return {
        "phase_unbalance_pct": round(unbalance_pct, 3),
        "voltage_instability":  round(cv, 3),
    }
