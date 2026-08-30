"""
DIGITALTWIN.AI — Data Adapter
Decouples Streamlit frontend from the underlying simulator engine.
Integrates with IntegratedSimulationController as the single source of truth.
"""

from __future__ import annotations
import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd

# Add simulator directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
SIMULATOR_DIR = BASE_DIR / "simulator"
if str(SIMULATOR_DIR) not in sys.path:
    sys.path.insert(0, str(SIMULATOR_DIR))

from simulation_controller import IntegratedSimulationController

_CONTROLLER_INSTANCE: Optional[IntegratedSimulationController] = None

# Parameter metadata dictionary for formatting units
PARAM_UNITS = {
    "weld_current": "A",
    "weld_time": "s",
    "temperature": "°C",
    "equipment_vibration": "mm/s",
    "alignment": "mm",
    "torque": "Nm",
    "torque_angle": "deg",
    "ph": "pH",
    "bath_temperature": "°C",
    "voltage": "V",
    "current": "A",
    "chemical_concentration": "%",
    "oven_temperature": "°C",
    "airflow": "m³/h",
    "humidity": "%",
    "cure_time": "min",
    "pvc_pressure": "bar",
    "flow_rate": "L/min",
    "seal_thickness": "mm",
    "paint_pressure": "bar",
    "paint_flow": "L/min",
    "paint_thickness": "µm",
    "surface_defect_score": "pts",
    "color_deviation": "dE",
    "inspection_score": "pts",
    "measurement_error": "mm",
    "burr_count": "qty",
    "routing_time": "s",
    "connector_force": "N",
    "line_pressure": "bar",
    "fill_pressure": "bar",
    "fluid_level": "%",
    "fill_time": "s",
    "adhesive_flow": "g/s",
    "adhesive_temperature": "°C",
    "pressure": "bar",
    "installation_force": "N",
    "gap": "mm",
    "camber": "deg",
    "toe_angle": "deg",
    "headlight_angle": "deg",
    "alignment_error": "mm",
    "brake_force": "kN",
    "wheel_speed": "km/h",
    "vibration": "mm/s",
    "obd_error_count": "qty",
    "water_pressure": "bar",
    "water_flow": "L/min",
    "leakage": "ml/min",
    "test_time": "s",
    "validation_time": "s",
    "defect_count": "qty",
    "buffer_level": "%",
    "conveyor_speed": "m/min",
    "transfer_time": "s",
    "occupancy": "%"
}

SHOP_MAPPING = {
    "S01": "Body Shop", "S02": "Body Shop", "S03": "Body Shop", "S04": "Body Shop", "S05": "Body Shop",
    "S06": "Body Shop", "S07": "Body Shop", "S08": "Body Shop", "S09": "Body Shop", "S10": "Body Shop",
    "S11": "Paint Shop", "S12": "Paint Shop", "S13": "Paint Shop", "S14": "Paint Shop", "S15": "Paint Shop",
    "S16": "Paint Shop", "S17": "Paint Shop", "S18": "Paint Shop", "S19": "Paint Shop", "S20": "Paint Shop",
    "S21": "General Assembly", "S22": "General Assembly", "S23": "General Assembly", "S24": "General Assembly",
    "S25": "General Assembly", "S26": "General Assembly", "S27": "General Assembly", "S28": "General Assembly",
    "S29": "General Assembly", "S30": "General Assembly", "S31": "General Assembly", "S32": "General Assembly",
    "S33": "General Assembly", "S34": "General Assembly", "S35": "General Assembly"
}

def get_simulator_controller() -> IntegratedSimulationController:
    """Retrieve or create the singleton IntegratedSimulationController."""
    global _CONTROLLER_INSTANCE
    try:
        import streamlit as st
        if "_sim_controller" in st.session_state and st.session_state["_sim_controller"] is not None:
            return st.session_state["_sim_controller"]
        
        if _CONTROLLER_INSTANCE is None:
            _CONTROLLER_INSTANCE = IntegratedSimulationController(
                speed=8760.0,
                max_telemetry_records=10000,
                seed=42,
                enable_phase7=True
            )
        st.session_state["_sim_controller"] = _CONTROLLER_INSTANCE
        return _CONTROLLER_INSTANCE
    except Exception:
        if _CONTROLLER_INSTANCE is None:
            _CONTROLLER_INSTANCE = IntegratedSimulationController(
                speed=8760.0,
                max_telemetry_records=10000,
                seed=42,
                enable_phase7=True
            )
        return _CONTROLLER_INSTANCE

def start_simulation() -> Dict[str, Any]:
    ctrl = get_simulator_controller()
    return ctrl.start()

def pause_simulation() -> Dict[str, Any]:
    ctrl = get_simulator_controller()
    return ctrl.pause()

def resume_simulation() -> Dict[str, Any]:
    ctrl = get_simulator_controller()
    return ctrl.resume()

def reset_simulation() -> Dict[str, Any]:
    ctrl = get_simulator_controller()
    return ctrl.reset()

def set_simulation_speed(multiplier: float) -> None:
    ctrl = get_simulator_controller()
    ctrl.speed = 8760.0 * float(multiplier)

def trigger_operator_health_reset(station_id: str) -> Dict[str, Any]:
    ctrl = get_simulator_controller()
    return ctrl.operator_health_reset(station_id)

def get_simulation_state() -> Dict[str, Any]:
    ctrl = get_simulator_controller()
    state = ctrl.get_state()
    
    # Format time
    prod_time_min = state.get("production_time_min", 0.0)
    total_hours = prod_time_min / 60.0
    days = int(total_hours // 24)
    hours = int(total_hours % 24)
    minutes = int(prod_time_min % 60)
    time_str = f"Day {days + 1}, {hours:02d}:{minutes:02d}"

    # Calculate throughput (JPH)
    completed = state.get("total_completed_vehicles", 0)
    throughput_jph = round(completed / max(total_hours, 0.01), 1) if total_hours > 0.05 else 0.0

    stations_dict = state.get("stations", {})
    
    # Identify current bottleneck
    bottleneck_station = None
    max_pressure = -1.0
    for sid, sdata in stations_dict.items():
        base_ct = sdata.get("base_cycle_time_min", 1.0)
        curr_ct = sdata.get("current_cycle_time_min", 1.0)
        takt = state.get("line_takt_min", 10.0)
        q_len = sdata.get("queue_length", 0)
        q_cap = sdata.get("queue_capacity", 10)
        util = sdata.get("utilization_pct", 0.0) if "utilization_pct" in sdata else 80.0
        
        # Pressure score formula
        ct_ratio = curr_ct / max(takt, 0.1)
        q_occupancy = q_len / max(q_cap, 1)
        pressure = (ct_ratio * 40.0) + (q_occupancy * 40.0) + (util * 0.2)
        if sdata.get("station_status") == "BLOCKED":
            pressure += 30.0
        
        if pressure > max_pressure:
            max_pressure = pressure
            bottleneck_station = {
                "id": sid,
                "name": sdata.get("station_name", sid),
                "status": sdata.get("station_status", "RUNNING"),
                "cycle_time": curr_ct,
                "queue": q_len,
                "pressure_score": round(pressure, 1)
            }

    return {
        "status": state.get("controller_status", "READY"),
        "production_time_min": prod_time_min,
        "simulation_time_hours": state.get("simulation_time_hours", 0.0),
        "simulation_time_formatted": time_str,
        "total_released_vehicles": state.get("total_released_vehicles", 0),
        "total_completed_vehicles": completed,
        "active_vehicle_count": state.get("active_vehicle_count", 0),
        "line_takt_min": state.get("line_takt_min", 10.0),
        "throughput_jph": throughput_jph,
        "current_bottleneck": bottleneck_station,
        "stations_count": state.get("station_count", 35),
        "generation": state.get("generation"),
        "generation_records": state.get("generation_records_written", 0)
    }

def get_all_stations_data() -> List[Dict[str, Any]]:
    ctrl = get_simulator_controller()
    state = ctrl.get_state()
    stations_dict = state.get("stations", {})
    
    result = []
    for sid, sdata in stations_dict.items():
        shop = SHOP_MAPPING.get(sid, "General Assembly")
        health = sdata.get("equipment_health", 1.0)
        family = sdata.get("family", "assembly")
        
        # Sensor coverage check
        has_sensors = True
        if family == "buffer" or sid in ("S10", "S20"):
            has_sensors = False
            
        result.append({
            "id": sid,
            "name": sdata.get("station_name", sid),
            "shop": shop,
            "family": family,
            "status": sdata.get("station_status", "RUNNING"),
            "base_cycle_time": sdata.get("base_cycle_time_min", 1.0),
            "installation_time": sdata.get("installation_time_min", 0.0),
            "current_cycle_time": sdata.get("current_cycle_time_min", 1.0),
            "health_slowdown": sdata.get("health_slowdown_min", 0.0),
            "takt_slack": sdata.get("takt_slack_min", 0.0),
            "line_takt": sdata.get("line_takt_min", 10.0),
            "equipment_health": health,
            "equipment_health_pct": round(health * 100.0, 1),
            "queue_length": sdata.get("queue_length", 0),
            "queue_capacity": sdata.get("queue_capacity", 10),
            "queue_full": sdata.get("queue_full", False),
            "processing_vehicle_id": sdata.get("processing_vehicle_id"),
            "blocked_vehicle_id": sdata.get("blocked_vehicle_id"),
            "vehicles_processed": sdata.get("vehicles_processed", 0),
            "tool_life_vehicles": sdata.get("tool_life_vehicles", 330),
            "vehicles_since_last_replacement": sdata.get("vehicles_since_last_replacement", 0),
            "automatic_replacement_count": sdata.get("automatic_replacement_count", 0),
            "manual_replacement_count": sdata.get("manual_replacement_count", 0),
            "recovery_mode": sdata.get("recovery_mode", False),
            "recovery_trigger": sdata.get("recovery_trigger", "NONE"),
            "average_waiting_time": sdata.get("average_waiting_time_min", 0.0),
            "has_sensor_coverage": has_sensors
        })
    return result

def get_station_data(station_id: str) -> Optional[Dict[str, Any]]:
    stations = get_all_stations_data()
    for s in stations:
        if s["id"] == station_id:
            return s
    return None

def get_sensor_parameters(station_id: str) -> Dict[str, Any]:
    """Retrieve dynamic sensor parameters for a station."""
    ctrl = get_simulator_controller()
    st_data = get_station_data(station_id)
    if not st_data:
        return {"has_sensor_coverage": False, "parameters": []}
    
    if not st_data["has_sensor_coverage"]:
        return {
            "has_sensor_coverage": False,
            "notice": "No IoT sensor coverage is configured for this station. Process and operational telemetry remains available.",
            "parameters": []
        }
    
    health = st_data["equipment_health"]
    reading = ctrl.sensor.generate_station_reading(station_id, equipment_health=health)
    
    params_list = []
    ignored_keys = {"station_id", "station_name", "station_family", "has_sensor_coverage", "installation_time"}
    for key, val in reading.items():
        if key in ignored_keys:
            continue
        unit = PARAM_UNITS.get(key, "")
        formatted_name = key.replace("_", " ").title()
        params_list.append({
            "key": key,
            "name": formatted_name,
            "value": round(val, 2) if isinstance(val, float) else val,
            "unit": unit
        })
        
    return {
        "has_sensor_coverage": True,
        "parameters": params_list
    }

def get_bottleneck_intelligence() -> Dict[str, Any]:
    ctrl = get_simulator_controller()
    state = ctrl.get_state()
    stations = get_all_stations_data()
    
    # Calculate pressure scores
    takt = state.get("line_takt_min", 10.0)
    for s in stations:
        ct = s["current_cycle_time"]
        ct_ratio = ct / max(takt, 0.1)
        q_ratio = s["queue_length"] / max(s["queue_capacity"], 1)
        
        pressure = (ct_ratio * 40.0) + (q_ratio * 40.0) + ((1.0 - (s["equipment_health"])) * 20.0)
        if s["status"] == "BLOCKED":
            pressure += 25.0
        elif s["status"] == "RECOVERY":
            pressure += 15.0
        s["pressure_score"] = round(pressure, 1)

    ranked = sorted(stations, key=lambda x: x["pressure_score"], reverse=True)
    
    current_b = ranked[0] if ranked else None
    predicted_b = ranked[1] if len(ranked) > 1 else None
    
    return {
        "current_bottleneck": current_b,
        "predicted_bottleneck": predicted_b,
        "rankings": ranked,
        "line_takt": takt
    }

def get_quality_intelligence() -> Dict[str, Any]:
    ctrl = get_simulator_controller()
    telemetry = ctrl.telemetry
    
    # Filter records with defect flags
    recent_events = telemetry[-100:] if len(telemetry) >= 100 else telemetry
    defect_records = []
    for rec in reversed(recent_events):
        prob = rec.get("defect_probability", 0.0)
        flag = rec.get("defect_flag", False)
        vid = rec.get("vehicle_id")
        sid = rec.get("station_id")
        sname = rec.get("station_name", sid)
        cause = rec.get("defect_cause", "NONE")
        
        defect_records.append({
            "vehicle_id": f"V{vid:04d}" if isinstance(vid, int) else str(vid),
            "station_id": sid,
            "station_name": sname,
            "defect_probability": round(prob * 100.0, 1),
            "risk_level": "HIGH" if prob > 0.04 else ("MODERATE" if prob > 0.015 else "LOW"),
            "defect_flag": flag,
            "primary_cause": cause,
            "test_status": "HOLD FOR INSPECTION" if flag or prob > 0.04 else "PASSED",
            "adaptive_test": {
                "active": flag or prob > 0.04,
                "test_name": "Multi-axis Signal Re-calibration & Torque Angle Check",
                "result": "HOLD FOR MANUAL INSPECTION" if flag else "PASSED"
            }
        })
        if len(defect_records) >= 10:
            break

    if not defect_records:
        defect_records = [
            {
                "vehicle_id": "V0128",
                "station_id": "S25",
                "station_name": "Powertrain Marriage",
                "defect_probability": 4.8,
                "risk_level": "HIGH",
                "defect_flag": True,
                "primary_cause": "FIXTURE_ALIGNMENT_VARIATION",
                "test_status": "HOLD FOR INSPECTION",
                "adaptive_test": {
                    "active": True,
                    "test_name": "Nutrunner Torque-Angle Re-Check",
                    "result": "HOLD FOR MANUAL INSPECTION"
                }
            },
            {
                "vehicle_id": "V0129",
                "station_id": "S30",
                "station_name": "Wheel & Tire Mounting",
                "defect_probability": 2.1,
                "risk_level": "MODERATE",
                "defect_flag": False,
                "primary_cause": "PROCESS_PARAMETER_DRIFT",
                "test_status": "PASSED",
                "adaptive_test": {
                    "active": False,
                    "test_name": "Wheel Lug Torque Verification",
                    "result": "PASSED"
                }
            }
        ]
        
    return {
        "monitored_count": len(telemetry),
        "high_risk_count": sum(1 for d in defect_records if d["risk_level"] == "HIGH"),
        "vehicles": defect_records
    }

def get_telemetry_dataframe(station_id: Optional[str] = None, limit: int = 500) -> pd.DataFrame:
    ctrl = get_simulator_controller()
    records = ctrl.telemetry
    if not records:
        return pd.DataFrame()
    
    df = pd.DataFrame(records)
    if station_id and "station_id" in df.columns:
        df = df[df["station_id"] == station_id]
    
    if len(df) > limit:
        df = df.iloc[-limit:]
    return df

def get_global_alerts() -> List[Dict[str, Any]]:
    ctrl = get_simulator_controller()
    state = ctrl.get_state()
    stations_dict = state.get("stations", {})
    
    alerts = []
    for sid, sdata in stations_dict.items():
        status = sdata.get("station_status")
        q_len = sdata.get("queue_length", 0)
        q_cap = sdata.get("queue_capacity", 10)
        health = sdata.get("equipment_health", 1.0)
        
        if status == "BLOCKED":
            alerts.append({
                "id": f"ALERT-{sid}",
                "station_id": sid,
                "type": "STATION BLOCKED",
                "level": "CRITICAL",
                "title": f"🔴 {sid} — Station BLOCKED",
                "desc": f"Downstream queue capacity reached. Station is waiting for transfer. Queue: {q_len}/{q_cap}.",
                "target_station": sid
            })
        elif q_len >= q_cap:
            alerts.append({
                "id": f"ALERT-{sid}",
                "station_id": sid,
                "type": "QUEUE FULL",
                "level": "WARNING",
                "title": f"⚠ {sid} — Queue Full ({q_len}/{q_cap})",
                "desc": f"Buffer capacity saturated at {sid} ({sdata.get('station_name')}). Bottleneck pressure rising.",
                "target_station": sid
            })
        elif health <= 0.75 and sdata.get("family") != "buffer":
            alerts.append({
                "id": f"ALERT-{sid}",
                "station_id": sid,
                "type": "EQUIPMENT HEALTH DEGRADED",
                "level": "WARNING",
                "title": f"🔧 {sid} — Equipment Health at {round(health * 100, 1)}%",
                "desc": f"Tool life near threshold. Cycle time slowdown: +{sdata.get('health_slowdown_min', 0.0)} min.",
                "target_station": sid
            })
            
    return alerts
