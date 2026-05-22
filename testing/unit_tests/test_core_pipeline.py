from alerts.alert_manager import AlertManager
from api.services.smart_grid_service import SmartGridService
from ml.health_score import calculate_health_score
from server.telemetry_manager import TelemetryManager
from smart_grid.fault_isolation import isolate_faults
from smart_grid.load_balancer import LoadBalancer


def sample_packet(**overrides):
    packet = {
        "substation_id": "S1",
        "timestamp": "2026-05-22T12:00:00",
        "voltage": 230.0,
        "current": 14.0,
        "temperature": 60.0,
        "harmonic_5th": 2.0,
        "load_percentage": 45.0,
    }
    packet.update(overrides)
    return packet


def test_telemetry_manager_tracks_latest_and_history():
    manager = TelemetryManager(history_window=2)

    manager.update(sample_packet(load_percentage=40))
    manager.update(sample_packet(load_percentage=50))
    manager.update(sample_packet(load_percentage=60))

    assert manager.substation_count() == 1
    assert manager.get_latest("S1")["load_percentage"] == 60
    assert [p["load_percentage"] for p in manager.get_history("S1")] == [50, 60]


def test_fault_isolation_and_health_score_for_critical_packet():
    packet = sample_packet(
        voltage=180,
        current=27,
        temperature=102,
        harmonic_5th=10,
        load_percentage=86,
    )

    faults = isolate_faults(packet)
    score, status = calculate_health_score(packet, is_anomaly=True)

    assert {f["name"] for f in faults["faults_detected"]} >= {"Overheat", "Voltage Sag", "Overload"}
    assert faults["highest_severity"] == "HIGH"
    assert status == "Critical"
    assert score < 50


def test_load_balancer_reduces_critical_substation_load():
    balancer = LoadBalancer()

    distribution = balancer.redistribute(
        ["S1", "S2", "S3"],
        {
            "S1": {"risk_level": "Critical"},
            "S2": {"risk_level": "Healthy"},
            "S3": {"risk_level": "Healthy"},
        },
    )

    assert distribution["S1"] == 10.0
    assert distribution["S2"] == 45.0
    assert distribution["S3"] == 45.0
    assert round(sum(distribution[sub] for sub in ["S1", "S2", "S3"]), 1) == 100.0


def test_smart_grid_service_returns_full_state_snapshot():
    class FakeServer:
        telemetry_data = {"S1": sample_packet()}
        health_data = {"S1": {"health_score": 95, "risk_level": "Healthy"}}
        fault_reports = {"S1": {"fault_count": 0}}
        predictions = {}
        redistribution_engine = None
        alert_manager = AlertManager()
        balancer = LoadBalancer()

    state = SmartGridService(FakeServer()).get_full_state()

    assert state["substation_count"] == 1
    assert state["telemetry"]["S1"]["voltage"] == 230.0
    assert state["health"]["S1"]["risk_level"] == "Healthy"
