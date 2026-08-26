import sys
import os

BASE_DIR = "/Users/apurba/.gemini/antigravity/scratch/digitaltwin_ai"
sys.path.insert(0, BASE_DIR)

from config.stations import STATIONS_CONFIG, STATIONS_BY_ID, SHOPS
from data.mock_data import SIM_ENGINE
from data.data_adapter import (
    get_simulation_state,
    get_all_stations_data,
    get_station_data,
    get_sensor_parameters,
    get_kpis,
    get_bottleneck_predictions,
    get_quality_predictions,
    get_vehicle_quality_detail,
    get_analytics_data,
    get_model_metadata,
    get_global_alerts,
    set_simulation_running,
    step_simulation,
    reset_simulation,
)

def test_all():
    print("Testing station configurations...")
    assert len(STATIONS_CONFIG) == 35, f"Expected 35 stations, got {len(STATIONS_CONFIG)}"
    assert len(STATIONS_BY_ID) == 35
    assert len(SHOPS) == 3
    print("✓ Station config verified: 35 stations across 3 shops.")

    print("Testing simulation state & reset...")
    reset_simulation()
    state = get_simulation_state()
    assert state["running"] == False
    assert state["tick"] == 0
    print("✓ Initial state verified.")

    print("Testing station telemetry generation...")
    stations = get_all_stations_data()
    assert len(stations) == 35
    for s in stations:
        assert "id" in s
        assert "name" in s
        assert "shop" in s
        assert "category" in s
        assert "status" in s
        assert "cycle_time" in s
        assert "queue_length" in s
        assert "parameters" in s
        assert len(s["parameters"]) > 0
    print("✓ All 35 stations have valid telemetry and dynamic parameters.")

    print("Testing KPIs (Verifying NO OEE)...")
    kpis = get_kpis()
    assert "production_actual" in kpis
    assert "production_target" in kpis
    assert "throughput_jph" in kpis
    assert "current_bottleneck" in kpis
    assert "overall_defect_risk" in kpis
    assert "oee" not in kpis and "OEE" not in str(kpis)
    print("✓ KPIs verified (No OEE present).")

    print("Testing Bottleneck Predictions...")
    bp = get_bottleneck_predictions()
    assert "current_bottleneck" in bp
    assert "predicted_bottleneck" in bp
    assert len(bp["rankings"]) > 0
    print("✓ Bottleneck predictions verified.")

    print("Testing Quality Predictions...")
    qp = get_quality_predictions()
    assert qp["monitored_count"] > 0
    assert len(qp["vehicles"]) > 0
    v128 = get_vehicle_quality_detail("V128")
    assert v128 is not None
    assert v128["adaptive_test"]["active"] == True
    print("✓ Quality predictions & Adaptive test verified.")

    print("Testing simulation steps & degradation progression...")
    set_simulation_running(True)
    for _ in range(15):
        step_simulation()
    state_after = get_simulation_state()
    assert state_after["tick"] == 15
    s25 = get_station_data("S25")
    assert s25["cycle_time"] > 14.0
    assert s25["status"] in ["WARNING", "CRITICAL"]
    print(f"✓ Progression verified: S25 degraded to status {s25['status']} (CT: {s25['cycle_time']}m, Risk: {s25['bottleneck_risk']}%).")

    alerts = get_global_alerts()
    assert len(alerts) > 0
    print(f"✓ Global alert system verified: {len(alerts)} active alerts.")

    model_info = get_model_metadata()
    assert "accuracy" not in model_info and "f1" not in model_info
    print("✓ Model metadata verified (No fabricated ML metrics).")

    print("\nALL LOGIC UNIT TESTS PASSED SUCCESSFULLY! 🎉")

if __name__ == "__main__":
    test_all()
