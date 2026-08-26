"""
Data Adapter Interface for DigitalTwin.ai.
Decouples UI from the underlying simulator and ML model outputs.
Allows future real simulator and ML pipelines to replace mock data seamlessly.
"""

from typing import Dict, List, Any, Optional
from data.mock_data import SIM_ENGINE, SimulationEngine
from config.stations import STATIONS_CONFIG, STATIONS_BY_ID

def get_simulation_state() -> Dict[str, Any]:
    """Retrieve high-level simulation state and speed."""
    return {
        "running": SIM_ENGINE.running,
        "speed": SIM_ENGINE.speed,
        "tick": SIM_ENGINE.tick,
        "status_label": "LIVE" if SIM_ENGINE.running else ("PAUSED" if SIM_ENGINE.tick > 0 else "STOPPED"),
        "status_class": "live" if SIM_ENGINE.running else ("paused" if SIM_ENGINE.tick > 0 else "stopped")
    }

def set_simulation_running(running: bool):
    """Start or pause the simulation."""
    SIM_ENGINE.running = running

def set_simulation_speed(speed: int):
    """Set simulation tick multiplier (1, 2, 5)."""
    SIM_ENGINE.speed = speed

def reset_simulation():
    """Reset simulation engine to initial state."""
    SIM_ENGINE.reset()

def step_simulation():
    """Advance simulation one tick."""
    SIM_ENGINE.step()

def get_kpis() -> Dict[str, Any]:
    """
    Retrieve top KPI summary metrics for the plant overview.
    NOTE: Strict adherence to 'NO OEE' rule.
    """
    actual_prod = min(150, 138 + int(SIM_ENGINE.tick * 0.4))
    target_prod = 150
    tp = round(max(38.0, 43.5 - (min(20, SIM_ENGINE.tick) * 0.12)), 1)
    
    # Identify active bottleneck
    all_stations = SIM_ENGINE.get_all_stations_state()
    critical_stations = [s for s in all_stations if s["status"] == "CRITICAL"]
    warning_stations = [s for s in all_stations if s["status"] == "WARNING"]
    
    if critical_stations:
        curr_b = f"{critical_stations[0]['id']} — {critical_stations[0]['name']}"
        b_class = "critical"
    elif warning_stations:
        curr_b = f"{warning_stations[0]['id']} — {warning_stations[0]['name']}"
        b_class = "warning"
    else:
        curr_b = "None (Nominal Flow)"
        b_class = "success"

    return {
        "production_actual": actual_prod,
        "production_target": target_prod,
        "production_pct": round((actual_prod / target_prod) * 100, 1),
        "throughput_jph": tp,
        "throughput_delta": "+1.2 vs shift avg" if tp >= 42.0 else "-1.5 vs shift avg",
        "current_bottleneck": curr_b,
        "current_bottleneck_class": b_class,
        "overall_defect_risk": "4.2%",
        "defect_risk_level": "MODERATE",
        "defect_risk_class": "warning"
    }

def get_all_stations_data() -> List[Dict[str, Any]]:
    """Retrieve normalized state for all 35 stations."""
    return SIM_ENGINE.get_all_stations_state()

def get_station_data(station_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve normalized data for a specific station."""
    all_stations = SIM_ENGINE.get_all_stations_state()
    for s in all_stations:
        if s["id"] == station_id:
            return s
    return None

def get_sensor_parameters(station_id: str) -> List[Dict[str, Any]]:
    """Retrieve dynamic sensor/process parameters for a station."""
    st = get_station_data(station_id)
    if st:
        return st.get("parameters", [])
    return []

def get_bottleneck_predictions() -> Dict[str, Any]:
    """Retrieve current, predicted bottlenecks, and risk rankings."""
    all_stations = SIM_ENGINE.get_all_stations_state()
    ranked = sorted(all_stations, key=lambda x: x["bottleneck_risk"], reverse=True)
    
    # Current Primary Bottleneck
    s25 = get_station_data("S25")
    # Secondary Predicted Bottleneck
    s18 = get_station_data("S18")
    
    return {
        "current_bottleneck": {
            "id": s25["id"] if s25 else "S25",
            "name": s25["name"] if s25 else "Marriage / Powertrain Integration",
            "risk_score": s25["bottleneck_risk"] if s25 else 91.0,
            "risk_level": s25["bottleneck_level"] if s25 else "CRITICAL",
            "cycle_time": s25["cycle_time"] if s25 else 13.4,
            "cycle_time_dev": s25["cycle_time_dev"] if s25 else 34.0,
            "queue_length": s25["queue_length"] if s25 else 5,
            "utilization": s25["utilization"] if s25 else 94,
            "status": s25["status"] if s25 else "CRITICAL"
        },
        "predicted_bottleneck": {
            "id": s18["id"] if s18 else "S18",
            "name": s18["name"] if s18 else "Final Paint Baking Oven",
            "risk_score": s18["bottleneck_risk"] if s18 else 68.0,
            "risk_level": s18["bottleneck_level"] if s18 else "WARNING",
            "predicted_time": s18["bottleneck_predicted_time"] if s18 else "~18 mins",
            "cycle_time": s18["cycle_time"] if s18 else 17.2,
            "queue_length": s18["queue_length"] if s18 else 4,
            "utilization": s18["utilization"] if s18 else 93
        },
        "rankings": [
            {
                "rank": idx + 1,
                "id": s["id"],
                "name": s["name"],
                "shop": s["shop"],
                "risk_score": s["bottleneck_risk"],
                "risk_level": s["bottleneck_level"],
                "cycle_time": s["cycle_time"],
                "queue_length": s["queue_length"],
                "utilization": s["utilization"],
                "status": s["status"]
            }
            for idx, s in enumerate(ranked[:8])
        ]
    }

def get_quality_predictions() -> Dict[str, Any]:
    """Retrieve ML quality prediction summary and tracked vehicles."""
    vehicles = SIM_ENGINE.get_tracked_vehicles()
    high_risk = [v for v in vehicles if v["risk_level"] == "HIGH"]
    active_tests = [v for v in vehicles if v["adaptive_test"]["active"]]
    
    return {
        "monitored_count": 48,
        "high_risk_count": len(high_risk),
        "tests_active_count": len(active_tests),
        "vehicles": vehicles
    }

def get_vehicle_quality_detail(vehicle_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve detailed defect signals and adaptive test data for a vehicle."""
    vehicles = SIM_ENGINE.get_tracked_vehicles()
    for v in vehicles:
        if v["vehicle_id"] == vehicle_id:
            return v
    return vehicles[0] if vehicles else None

def get_analytics_data(shop_filter: Optional[str] = None, station_filter: Optional[str] = None, time_window: str = "4h") -> Dict[str, Any]:
    """Retrieve historical trend series for charting."""
    return {
        "timestamps": SIM_ENGINE.history_timestamps,
        "throughput": SIM_ENGINE.history_throughput,
        "cycle_times": SIM_ENGINE.history_cycle_times,
        "queues": SIM_ENGINE.history_queues
    }

def get_model_metadata() -> Dict[str, Any]:
    """
    Retrieve model metadata.
    NOTE: Strict adherence to 'DO NOT fabricate accuracy, precision, recall, F1' rule.
    """
    return {
        "status": "Prototype / Staging",
        "training_data": "Synthetic telemetry & hardware-in-the-loop logs",
        "model_type": "Temporal Graph Neural Network (TGNN) + Random Forest Ensemble (To be connected)",
        "inference_latency": "14 ms (Target)",
        "features_tracked": "Cycle time deviation, vibration harmonics, motor current draw, queue surge velocity, weld thermal delta",
        "last_retrained": "2026-08-20 (Simulated baseline)"
    }

def get_global_alerts() -> List[Dict[str, Any]]:
    """Retrieve active system warnings and critical alerts."""
    alerts = []
    s25 = get_station_data("S25")
    if s25 and s25["status"] in ["WARNING", "CRITICAL"]:
        alerts.append({
            "id": "ALERT-S25",
            "station_id": "S25",
            "type": "BOTTLENECK RISK",
            "level": s25["status"],
            "title": f"⚠ S25 BOTTLENECK RISK — Cycle time increasing (+{s25['cycle_time_dev']}%)",
            "desc": f"Predicted critical in {s25['bottleneck_predicted_time']}. Queue length is {s25['queue_length']}/{s25['buffer_capacity']} units. Operator inspection recommended.",
            "target_station": "S25"
        })
    s30 = get_station_data("S30")
    if s30 and s30["quality_level"] == "HIGH":
        alerts.append({
            "id": "ALERT-S30",
            "station_id": "S30",
            "type": "QUALITY ANOMALY",
            "level": "WARNING",
            "title": "⚡ S30 DEFECT ANOMALY — Adaptive Quality Test Activated on Vehicle V128",
            "desc": "Nutrunner torque/angle variation detected. Adaptive test sequence triggered; hold for buyoff.",
            "target_station": "S30"
        })
    return alerts
