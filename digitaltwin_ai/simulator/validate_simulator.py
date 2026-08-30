"""
DigitalTwin.ai - FULL YEAR VALIDATION
"""

from __future__ import annotations

import csv
import importlib.util
import io
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

BASE_DIR = Path(__file__).resolve().parent

VALIDATION_DIR = BASE_DIR / "validation"
CONFIG_PATH = BASE_DIR / "phase1_station_config.json"

PHASE4_PATH = BASE_DIR / "phase4_incremental_line_engine.py"
PHASE2_PATH = BASE_DIR / "phase2_sensor_engine.py"
PHASE5_PATH = BASE_DIR / "phase5_telemetry_generator.py"
DEFECT_PATH = BASE_DIR / "defect_model.py"

REAL_YEAR_MINUTES = 365 * 24 * 60

SPECIAL_QUEUE_CAPACITY = {
    "S10": 50,
    "S20": 50,
}

def load_module(name: str, path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Required module not found: {path}")
    spec = importlib.util.spec_from_file_location(name, str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

def next_run_number() -> int:
    VALIDATION_DIR.mkdir(parents=True, exist_ok=True)
    numbers = []
    for path in VALIDATION_DIR.iterdir():
        if not path.is_dir(): continue
        name = path.name.lower()
        if name.startswith("year") and name.endswith("_data"):
            value = name[4:-5]
            if value.isdigit(): numbers.append(int(value))
    return max(numbers) + 1 if numbers else 1

def create_run_directory():
    number = next_run_number()
    while True:
        directory = VALIDATION_DIR / f"year{number}_data"
        try:
            directory.mkdir(parents=True, exist_ok=False)
            return number, directory
        except FileExistsError:
            number += 1

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def clean_record(record: Dict[str, Any]) -> Dict[str, Any]:
    output = {}
    for key, value in record.items():
        if isinstance(value, bool):
            output[key] = value
        elif isinstance(value, (int, float)):
            if key == "simulation_time_hours":
                output[key] = round(float(value), 8)
            else:
                output[key] = round(float(value), 3)
        else:
            output[key] = value
    return output

def write_csv(path: Path, rows: List[Dict[str, Any]]):
    fields = []
    for row in rows:
        for key in row:
            if key not in fields: fields.append(key)
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
    if fields:
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})
    path.write_text(buffer.getvalue(), encoding="utf-8", newline="")

def write_json(path: Path, payload: Any):
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8", newline="")

def station_metadata(config: Dict[str, Any]):
    return {
        station["id"]: {
            "station_id": station["id"],
            "station_name": station["name"],
            "station_family": station["family"],
            "equipment_driven": station.get("equipment_driven", False),
        }
        for station in config["stations"]
    }

def validate_records(records: List[Dict[str, Any]], metadata: Dict[str, Dict[str, Any]]):
    failures = []
    if not records: return ["No telemetry records generated."]

    required = {
        "vehicle_id", "station_id", "station_name", "station_family",
        "simulation_time_hours", "arrival_time_min", "start_time_min", "completion_time_min",
        "waiting_time_min", "base_cycle_time_min", "installation_time_min", "health_slowdown_min",
        "cycle_time_min", "ctd_min", "equipment_health", "queue_length", "queue_capacity",
        "utilization_pct", "station_status", "maintenance_active", "tool_replacement_event",
        "tool_replacement_number", "defect_present", "defect_introduced_here", "defect_detected",
        "defect_cause", "defect_type", "defect_severity", "defect_risk_score", "defect_probability",
        "defect_source_station", "process_drift_score", "input_variation_score",
        "fixture_alignment_score", "environmental_deviation_score",
    }

    missing = required - set(records[0].keys())
    if missing:
        failures.append("Missing telemetry fields: " + ", ".join(sorted(missing)))
        return failures

    station_ids = {row["station_id"] for row in records}
    if len(station_ids) != 35: failures.append(f"Expected 35 stations, found {len(station_ids)}.")

    defect_count, introduced_count, detected_count = 0, 0, 0
    replacement_numbers = defaultdict(set)

    for index, row in enumerate(records):
        sid = row["station_id"]
        if sid not in metadata:
            failures.append(f"Unknown station {sid} at record {index}.")
            break

        capacity = 50 if sid in SPECIAL_QUEUE_CAPACITY else 10
        if int(row["queue_capacity"]) != capacity:
            failures.append(f"{sid}: queue_capacity={row['queue_capacity']} but expected {capacity}.")
            break

        queue = float(row["queue_length"])
        if not 0.0 <= queue <= capacity:
            failures.append(f"{sid}: queue_length={queue} outside [0,{capacity}].")
            break

        health = float(row["equipment_health"])
        if sid in SPECIAL_QUEUE_CAPACITY:
            if abs(health - 1.0) > 0.0001:
                failures.append(f"{sid}: buffer health must remain 1.0.")
                break
            if bool(row["defect_present"]) or bool(row["defect_introduced_here"]) or bool(row["defect_detected"]):
                failures.append(f"{sid}: buffer must never contain defects.")
                break
            if float(row["defect_severity"]) != 0.0:
                failures.append(f"{sid}: buffer defect severity must be 0.")
                break
            if bool(row["tool_replacement_event"]):
                failures.append(f"{sid}: buffer must never have tool replacement.")
                break

        if not 0.0 <= health <= 1.0:
            failures.append(f"{sid}: health outside [0,1].")
            break

        utilization = float(row["utilization_pct"])
        if not 0.0 <= utilization <= 100.0:
            failures.append(f"{sid}: utilization outside [0,100].")
            break

        if float(row["waiting_time_min"]) < -0.001:
            failures.append(f"{sid}: negative waiting time.")
            break

        if float(row["cycle_time_min"]) < 0:
            failures.append(f"{sid}: negative cycle time.")
            break

        risk = float(row["defect_risk_score"])
        probability = float(row["defect_probability"])
        severity = float(row["defect_severity"])

        if not 0.0 <= risk <= 1.0: failures.append(f"{sid}: defect risk outside [0,1]."); break
        if not 0.0 <= probability <= 1.0: failures.append(f"{sid}: defect probability outside [0,1]."); break

        present = bool(row["defect_present"])
        introduced = bool(row["defect_introduced_here"])
        detected = bool(row["defect_detected"])

        if detected and not present:
            failures.append(f"{sid}: defect_detected=True while defect_present=False.")
            break
        if introduced and detected:
            failures.append(f"{sid}: defect_introduced_here=True and defect_detected=True on same non-inspection.")
            break

        if present:
            defect_count += 1
            if severity <= 0:
                failures.append(f"{sid}: defect_present=True requires positive severity.")
                break
            if row["defect_cause"] in {"", "NONE", None}:
                failures.append(f"{sid}: present defect has no cause.")
                break
            if row["defect_type"] in {"", "NONE", None}:
                failures.append(f"{sid}: present defect has no type.")
                break
        else:
            if abs(severity) > 0.0001:
                failures.append(f"{sid}: defect_present=False but severity={severity}.")
                break

        if introduced: introduced_count += 1
        if detected: detected_count += 1

        replacement = bool(row["tool_replacement_event"])
        number = int(row["tool_replacement_number"])

        if replacement:
            if number < 1:
                failures.append(f"{sid}: replacement event must have number >= 1.")
                break
            replacement_numbers[sid].add(number)
        elif number != 0:
            failures.append(f"{sid}: replacement_number must be 0 when no replacement event.")
            break

    return failures

def build_summary(records: List[Dict[str, Any]]):
    grouped = defaultdict(list)
    for row in records: grouped[row["station_id"]].append(row)
    output = []
    for sid, rows in grouped.items():
        def nums(field): return [float(row.get(field, 0)) for row in rows]
        cts, waits = nums("cycle_time_min"), nums("waiting_time_min")
        queues, health = nums("queue_length"), nums("equipment_health")
        utilization, risks, probabilities = nums("utilization_pct"), nums("defect_risk_score"), nums("defect_probability")

        output.append({
            "station_id": sid, "station_name": rows[0]["station_name"], "station_family": rows[0]["station_family"],
            "queue_capacity": int(rows[0]["queue_capacity"]), "records": len(rows),
            "average_cycle_time_min": round(sum(cts) / len(cts), 3), "max_cycle_time_min": round(max(cts), 3),
            "average_queue_length": round(sum(queues) / len(queues), 3), "max_queue_length": int(max(queues)),
            "average_waiting_time_min": round(sum(waits) / len(waits), 3), "average_utilization_pct": round(sum(utilization) / len(utilization), 3),
            "average_equipment_health": round(sum(health) / len(health), 3), "minimum_equipment_health": round(min(health), 3),
            "average_defect_risk_score": round(sum(risks) / len(risks), 3), "average_defect_probability": round(sum(probabilities) / len(probabilities), 3),
            "defect_records": sum(bool(row.get("defect_present", False)) for row in rows),
            "defects_introduced_here": sum(bool(row.get("defect_introduced_here", False)) for row in rows),
            "detected_defects": sum(bool(row.get("defect_detected", False)) for row in rows),
        })
    output.sort(key=lambda row: row["station_id"])
    return output

def main() -> int:
    print("\nDIGITALTWIN.AI\nFULL YEAR VALIDATION\n" + "=" * 70)

    run_number, run_dir = create_run_directory()
    print(f"Validation run     : {run_number}\nOutput             : {run_dir}")

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    metadata = station_metadata(config)

    phase4 = load_module("validation_phase4", PHASE4_PATH)
    phase2 = load_module("validation_phase2", PHASE2_PATH)
    phase5 = load_module("validation_phase5", PHASE5_PATH)
    defect_module = load_module("validation_defect", DEFECT_PATH)

    engine = phase4.IncrementalLineEngine(CONFIG_PATH, seed=42)
    sensor_engine = phase2.SensorEngine(CONFIG_PATH, seed=42)
    defect_engine = defect_module.DefectEngine(CONFIG_PATH, seed=42)

    print(f"Stations configured : {len(metadata)}")
    print(f"Line takt           : {engine.line_takt_min:.3f} min")
    print("Simulation horizon  : 1 year")

    print("\nRunning full-year simulation...")
    engine.step(REAL_YEAR_MINUTES)
    events = engine.get_all_events()

    print(f"Operational events  : {len(events):,}")
    print("Generating sensors and defect labels...")

    event_rows = []
    sensor_rows = []
    for event in events:
        row = dict(event)
        row["simulation_time_hours"] = float(event["completion_time_min"]) / REAL_YEAR_MINUTES
        sensor = sensor_engine.generate_station_reading(event["station_id"], event["equipment_health"], 1.0)
        defect = defect_engine.evaluate(event["vehicle_id"], event["station_id"], sensor, event["equipment_health"])
        row.update(defect)
        sensor.update({"vehicle_id": event["vehicle_id"], "simulation_time_hours": row["simulation_time_hours"]})
        event_rows.append(row)
        sensor_rows.append(sensor)

    telemetry = phase5.build_telemetry(event_rows, sensor_rows, metadata)
    telemetry = [clean_record(row) for row in telemetry]
    print(f"Telemetry records   : {len(telemetry):,}")

    failures = validate_records(telemetry, metadata)
    summary = build_summary(telemetry)

    telemetry_path = run_dir / "assembly_line_telemetry.csv"
    summary_path = run_dir / "station_telemetry_summary.csv"
    schema_path = run_dir / "telemetry_schema.json"
    run_summary_path = run_dir / "validation_run_summary.json"

    write_csv(telemetry_path, telemetry)
    write_csv(summary_path, summary)

    fields = []
    for row in telemetry:
        for key in row:
            if key not in fields: fields.append(key)

    schema = {
        "dataset": f"DigitalTwin.ai validation run {run_number}",
        "validation_run": run_number, "simulation_horizon_hours": 1.0,
        "real_operation_years": 1, "real_year_minutes": REAL_YEAR_MINUTES,
        "station_count": len(metadata),
        "queue_capacity_rules": {"default": 10, "S10": 50, "S20": 50},
        "fields": fields,
        "precision": {"general_numeric": 3, "simulation_time_hours": 8}
    }
    write_json(schema_path, schema)

    unique_vehicles = len({int(row["vehicle_id"]) for row in telemetry})

    run_summary = {
        "dataset": f"year{run_number}_data", "validation_run": run_number,
        "status": "PASS" if not failures else "FAIL", "generated_utc": utc_now(),
        "stations": len(metadata), "vehicles": unique_vehicles, "telemetry_records": len(telemetry),
        "simulation_time_hours": round(engine.current_time_min / REAL_YEAR_MINUTES, 8),
        "production_time_min": round(engine.current_time_min, 3),
        "validation_failures": failures,
    }
    write_json(run_summary_path, run_summary)

    print("\nVALIDATION\n" + "-" * 70)
    if failures:
        print("FAILED")
        for failure in failures: print(" -", failure)
    else:
        print("PASSED")

    return 0 if not failures else 1

if __name__ == "__main__":
    raise SystemExit(main())
