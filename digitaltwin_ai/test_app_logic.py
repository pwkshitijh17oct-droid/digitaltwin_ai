"""
DIGITALTWIN.AI — Automated Integration & Logic Test Suite
Verifies full simulator integration, station config correctness, data adapter API, and state preservation.
"""

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

import data.adapter as adapter

def run_tests():
    print("=" * 60)
    print("DIGITALTWIN.AI INTEGRATION TEST SUITE")
    print("=" * 60)

    # 1. Controller Singleton Initialization
    ctrl = adapter.get_simulator_controller()
    assert ctrl is not None, "Simulator Controller failed to initialize."
    print("[PASS] 1. Controller Singleton Initialization: PASSED")

    # 2. Simulation State & Station Count Verification
    state = adapter.get_simulation_state()
    assert state["status"] in ("READY", "RUNNING", "PAUSED"), f"Invalid status: {state['status']}"
    assert state["stations_count"] == 35, f"Expected 35 stations, got {state['stations_count']}"
    print("[PASS] 2. Simulation State & Station Count (35 Stations): PASSED")

    # 3. All 35 Stations Configuration & Order Match
    stations = adapter.get_all_stations_data()
    assert len(stations) == 35, f"Expected 35 station data objects, got {len(stations)}"
    station_ids = [s["id"] for s in stations]
    expected_ids = [f"S{i:02d}" for i in range(1, 36)]
    assert station_ids == expected_ids, f"Station order mismatch!\nExpected: {expected_ids}\nGot: {station_ids}"
    print("[PASS] 3. All 35 Stations Order & Names Match Config: PASSED")

    # 4. Station S25 Details & Equipment Health
    s25 = adapter.get_station_data("S25")
    assert s25 is not None, "Station S25 not found!"
    assert s25["name"] == "Powertrain Marriage", f"Unexpected S25 name: {s25['name']}"
    assert 0.0 <= s25["equipment_health"] <= 1.0, f"Invalid S25 health: {s25['equipment_health']}"
    print("[PASS] 4. Station S25 Details & Equipment Health: PASSED")

    # 5. Dynamic Sensor Coverage vs Sensorless Buffer
    s25_sensors = adapter.get_sensor_parameters("S25")
    assert s25_sensors["has_sensor_coverage"] is True, "S25 should have sensor coverage!"
    assert len(s25_sensors["parameters"]) > 0, "S25 should return dynamic parameters!"
    
    s10_sensors = adapter.get_sensor_parameters("S10")
    assert s10_sensors["has_sensor_coverage"] is False, "S10 (Buffer 1) should be marked sensorless!"
    print("[PASS] 5. Dynamic Sensor Coverage vs Sensorless Buffer: PASSED")

    # 6. Simulator Lifecycle: RUN, PAUSE, RESET
    res_start = adapter.start_simulation()
    assert res_start["controller_status"] == "RUNNING", f"Start failed: {res_start}"
    print("   -> Simulation RUNNING...")

    res_pause = adapter.pause_simulation()
    assert res_pause["controller_status"] == "PAUSED", f"Pause failed: {res_pause}"
    print("   -> Simulation PAUSED...")

    # 7. Operator Health Reset Action
    reset_res = adapter.trigger_operator_health_reset("S25")
    assert "health_after" in reset_res or "status" in reset_res or "station_id" in reset_res, f"Health reset unexpected response: {reset_res}"
    print("[PASS] 7. Operator Health Reset Action: PASSED")

    # 8. Bottleneck Intelligence Calculation
    b_intel = adapter.get_bottleneck_intelligence()
    assert b_intel["current_bottleneck"] is not None, "Bottleneck intelligence returned no current bottleneck!"
    assert len(b_intel["rankings"]) == 35, f"Expected 35 rankings, got {len(b_intel['rankings'])}"
    print("[PASS] 8. Bottleneck Intelligence Calculation: PASSED")

    # 9. Quality Intelligence Defect Evaluation
    q_intel = adapter.get_quality_intelligence()
    assert len(q_intel["vehicles"]) > 0, "Quality intelligence returned no vehicles!"
    print("[PASS] 9. Quality Intelligence Defect Evaluation: PASSED")

    # 10. Reset Simulation
    res_reset = adapter.reset_simulation()
    assert res_reset["controller_status"] == "READY", f"Reset failed: {res_reset}"
    print("[PASS] 10. Simulation RESET: PASSED")

    print("=" * 60)
    print("ALL 10 VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
