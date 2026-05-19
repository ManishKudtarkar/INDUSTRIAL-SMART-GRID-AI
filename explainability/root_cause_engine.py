"""
RootCauseEngine — maps detected faults to probable root causes.

Uses a rule-based knowledge base (easily extensible) combined with
SHAP explanations to produce human-readable root cause reports.
"""
from typing import Dict, Any, List

from smart_grid.fault_isolation import isolate_faults
from shared.utils import get_logger

logger = get_logger(__name__)


# ── Knowledge base ────────────────────────────────────────────────────────────
# Maps fault name → list of probable root causes with likelihood weights

FAULT_ROOT_CAUSES: Dict[str, List[Dict[str, Any]]] = {
    "Overheat": [
        {"cause": "Cooling system failure",          "likelihood": 0.40},
        {"cause": "Overloaded transformer windings", "likelihood": 0.30},
        {"cause": "Blocked ventilation",             "likelihood": 0.20},
        {"cause": "Ambient temperature spike",       "likelihood": 0.10},
    ],
    "Voltage Sag": [
        {"cause": "Heavy load connection on feeder", "likelihood": 0.35},
        {"cause": "Upstream fault or short circuit", "likelihood": 0.30},
        {"cause": "Capacitor bank failure",          "likelihood": 0.20},
        {"cause": "Transformer tap changer fault",   "likelihood": 0.15},
    ],
    "Voltage Surge": [
        {"cause": "Load shedding / sudden disconnection", "likelihood": 0.40},
        {"cause": "Lightning strike on feeder",           "likelihood": 0.30},
        {"cause": "Voltage regulator malfunction",        "likelihood": 0.30},
    ],
    "Overload": [
        {"cause": "Unexpected demand spike",              "likelihood": 0.45},
        {"cause": "Load redistribution from failed sub",  "likelihood": 0.30},
        {"cause": "Metering error / false reading",       "likelihood": 0.15},
        {"cause": "Scheduled maintenance overrun",        "likelihood": 0.10},
    ],
    "Harmonic Distortion": [
        {"cause": "Non-linear loads (VFDs, UPS, rectifiers)", "likelihood": 0.50},
        {"cause": "Transformer saturation",                   "likelihood": 0.25},
        {"cause": "Resonance with power factor capacitors",   "likelihood": 0.25},
    ],
    "Overcurrent": [
        {"cause": "Short circuit on downstream feeder", "likelihood": 0.50},
        {"cause": "Motor starting surge",               "likelihood": 0.30},
        {"cause": "Ground fault",                       "likelihood": 0.20},
    ],
}


class RootCauseEngine:
    def __init__(self, shap_explainer=None):
        """
        shap_explainer: optional ShapExplainer instance for ML-guided analysis.
        """
        self._shap = shap_explainer

    def analyse(self, packet: dict, health_record: dict) -> Dict[str, Any]:
        """
        Produce a root cause analysis report for a telemetry packet.

        Returns:
            {
                "substation_id": str,
                "faults": [...],
                "root_causes": [...],
                "shap_explanation": {...},
                "recommended_actions": [...]
            }
        """
        sub_id = packet.get("substation_id", "Unknown")
        fault_report = isolate_faults(packet)

        # Gather root causes for each detected fault
        all_causes: List[Dict[str, Any]] = []
        for fault in fault_report["faults_detected"]:
            causes = FAULT_ROOT_CAUSES.get(fault["name"], [])
            for c in causes:
                all_causes.append({
                    "fault":      fault["name"],
                    "cause":      c["cause"],
                    "likelihood": c["likelihood"],
                })

        # Sort by likelihood descending
        all_causes.sort(key=lambda x: x["likelihood"], reverse=True)

        # SHAP explanation
        shap_result = {}
        if self._shap and health_record.get("anomaly_detected"):
            shap_result = self._shap.explain(packet)

        # Recommended actions
        actions = self._recommend_actions(fault_report, health_record)

        return {
            "substation_id":      sub_id,
            "faults":             fault_report["faults_detected"],
            "highest_severity":   fault_report["highest_severity"],
            "root_causes":        all_causes[:5],   # top 5
            "shap_explanation":   shap_result,
            "recommended_actions": actions,
        }

    # ── private ───────────────────────────────────────────────────────────────

    def _recommend_actions(self, fault_report: dict, health_record: dict) -> List[str]:
        actions = []
        fault_names = {f["name"] for f in fault_report["faults_detected"]}

        if "Overheat" in fault_names:
            actions.append("Inspect and clean cooling fans / heat exchangers.")
            actions.append("Reduce load on affected transformer immediately.")
        if "Voltage Sag" in fault_names:
            actions.append("Check upstream feeder breakers and tap changer position.")
            actions.append("Deploy reactive power compensation (capacitor bank).")
        if "Overload" in fault_names:
            actions.append("Activate load redistribution to healthy substations.")
            actions.append("Shed non-critical loads if redistribution is insufficient.")
        if "Harmonic Distortion" in fault_names:
            actions.append("Install harmonic filters on non-linear load feeders.")
            actions.append("Check power factor correction capacitors for resonance.")
        if "Overcurrent" in fault_names:
            actions.append("Inspect downstream feeders for short circuits or ground faults.")
            actions.append("Verify protection relay settings and trip thresholds.")

        if health_record.get("health_score", 100) < 30:
            actions.insert(0, "URGENT: Consider emergency isolation of this substation.")

        return actions if actions else ["Monitor closely — no immediate action required."]
