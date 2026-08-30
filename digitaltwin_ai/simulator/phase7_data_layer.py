"""
DIGITALTWIN.AI
PHASE 7 - DATA LAYER / PERSISTENCE
"""

from __future__ import annotations

import csv
import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

BASE_DIR = Path(__file__).resolve().parent

OUTPUT_DIR = BASE_DIR / "phase7_output"

DEFAULT_DATABASE = OUTPUT_DIR / "digitaltwin_telemetry.db"
DEFAULT_CSV = OUTPUT_DIR / "telemetry.csv"
DEFAULT_JSONL = OUTPUT_DIR / "telemetry.jsonl"

def json_safe(value: Any) -> Any:
    if value is None: return None
    if isinstance(value, (str, int, float, bool)): return value
    if isinstance(value, (list, tuple, dict)):
        return json.dumps(value, separators=(",", ":"), ensure_ascii=False)
    return str(value)

def sqlite_value(value: Any) -> Any:
    if value is None: return None
    if isinstance(value, bool): return int(value)
    if isinstance(value, (str, int, float)): return value
    if isinstance(value, (list, tuple, dict)):
        return json.dumps(value, separators=(",", ":"), ensure_ascii=False)
    return str(value)

def normalise_record(record: Dict[str, Any]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in record.items():
        clean_key = str(key).strip()
        if not clean_key: continue
        result[clean_key] = value
    return result

class TelemetryDataLayer:
    def __init__(
        self,
        database_path: str | Path = DEFAULT_DATABASE,
        csv_path: str | Path = DEFAULT_CSV,
        jsonl_path: str | Path = DEFAULT_JSONL,
        enable_csv: bool = True,
        enable_jsonl: bool = True,
    ):
        self.database_path = Path(database_path)
        self.csv_path = Path(csv_path)
        self.jsonl_path = Path(jsonl_path)
        self.enable_csv = bool(enable_csv)
        self.enable_jsonl = bool(enable_jsonl)

        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        if self.enable_csv: self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        if self.enable_jsonl: self.jsonl_path.parent.mkdir(parents=True, exist_ok=True)

        self._lock = threading.RLock()
        self._csv_fields: List[str] = []
        self._records_written = 0
        self._create_database()
        self._load_existing_csv_fields()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(str(self.database_path), check_same_thread=False)
        connection.execute("PRAGMA journal_mode=WAL;")
        connection.execute("PRAGMA synchronous=NORMAL;")
        return connection

    def _create_database(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS telemetry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vehicle_id INTEGER,
                    station_id TEXT,
                    station_name TEXT,
                    station_family TEXT,
                    simulation_time_hours REAL,
                    arrival_time_min REAL,
                    start_time_min REAL,
                    completion_time_min REAL,
                    cycle_time_min REAL,
                    base_cycle_time_min REAL,
                    installation_time_min REAL,
                    ctd_min REAL,
                    queue_length REAL,
                    waiting_time_min REAL,
                    utilization_pct REAL,
                    station_status TEXT,
                    equipment_health REAL,
                    maintenance_active INTEGER,
                    equipment_driven INTEGER,
                    health_slowdown_min REAL,
                    defect_present INTEGER,
                    defect_introduced_here INTEGER,
                    defect_detected INTEGER,
                    defect_cause TEXT,
                    defect_type TEXT,
                    defect_severity REAL,
                    defect_risk_score REAL,
                    defect_source_station TEXT,
                    process_drift_score REAL,
                    input_variation_score REAL,
                    fixture_alignment_score REAL,
                    environmental_deviation_score REAL,
                    sensor_data_json TEXT,
                    record_created_utc TEXT
                )
                """
            )
            
            existing_columns = {row[1] for row in connection.execute("PRAGMA table_info(telemetry)").fetchall()}
            defect_columns = {
                "defect_present": "INTEGER", "defect_introduced_here": "INTEGER", "defect_detected": "INTEGER",
                "defect_cause": "TEXT", "defect_type": "TEXT", "defect_severity": "REAL",
                "defect_risk_score": "REAL", "defect_source_station": "TEXT", "process_drift_score": "REAL",
                "input_variation_score": "REAL", "fixture_alignment_score": "REAL", "environmental_deviation_score": "REAL",
            }
            for column, sql_type in defect_columns.items():
                if column not in existing_columns:
                    connection.execute(f"ALTER TABLE telemetry ADD COLUMN {column} {sql_type}")

            connection.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_vehicle ON telemetry(vehicle_id)")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_station ON telemetry(station_id)")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_time ON telemetry(simulation_time_hours)")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS simulation_runs (
                    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    started_utc TEXT NOT NULL,
                    completed_utc TEXT,
                    records_written INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'RUNNING'
                )
                """
            )
            connection.commit()

    def _load_existing_csv_fields(self) -> None:
        if not self.enable_csv or not self.csv_path.exists():
            self._csv_fields = []
            return
        try:
            with self.csv_path.open("r", newline="", encoding="utf-8") as file:
                reader = csv.reader(file)
                self._csv_fields = list(next(reader, []))
        except (OSError, csv.Error):
            self._csv_fields = []

    def _append_csv(self, records: List[Dict[str, Any]]) -> None:
        if not self.enable_csv or not records: return
        all_fields = list(self._csv_fields)
        for record in records:
            for key in record:
                if key not in all_fields: all_fields.append(key)
        
        schema_changed = (all_fields != self._csv_fields)
        if schema_changed and self.csv_path.exists():
            existing_rows: List[Dict[str, Any]] = []
            try:
                with self.csv_path.open("r", newline="", encoding="utf-8") as file:
                    existing_rows = list(csv.DictReader(file))
            except (OSError, csv.Error):
                existing_rows = []
                
            with self.csv_path.open("w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=all_fields, extrasaction="ignore")
                writer.writeheader()
                for row in existing_rows: writer.writerow(row)
                for record in records:
                    writer.writerow({field: record.get(field) for field in all_fields})
            self._csv_fields = all_fields
            return

        write_header = not self.csv_path.exists() or self.csv_path.stat().st_size == 0
        with self.csv_path.open("a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=all_fields, extrasaction="ignore")
            if write_header: writer.writeheader()
            for record in records:
                writer.writerow({field: record.get(field) for field in all_fields})
        self._csv_fields = all_fields

    def _append_jsonl(self, records: List[Dict[str, Any]]) -> None:
        if not self.enable_jsonl or not records: return
        with self.jsonl_path.open("a", encoding="utf-8") as file:
            for record in records:
                payload = dict(record)
                payload["record_created_utc"] = datetime.now(timezone.utc).isoformat()
                file.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def _database_row(self, record: Dict[str, Any]) -> tuple:
        known_columns = [
            "vehicle_id", "station_id", "station_name", "station_family", "simulation_time_hours",
            "arrival_time_min", "start_time_min", "completion_time_min", "cycle_time_min",
            "base_cycle_time_min", "installation_time_min", "ctd_min", "queue_length",
            "waiting_time_min", "utilization_pct", "station_status", "equipment_health",
            "maintenance_active", "equipment_driven", "health_slowdown_min", "defect_present",
            "defect_introduced_here", "defect_detected", "defect_cause", "defect_type",
            "defect_severity", "defect_risk_score", "defect_source_station", "process_drift_score",
            "input_variation_score", "fixture_alignment_score", "environmental_deviation_score",
        ]
        sensor_data = {key: value for key, value in record.items() if key not in known_columns}
        created = datetime.now(timezone.utc).isoformat()
        
        return (
            sqlite_value(record.get("vehicle_id")), sqlite_value(record.get("station_id")),
            sqlite_value(record.get("station_name")), sqlite_value(record.get("station_family")),
            sqlite_value(record.get("simulation_time_hours")), sqlite_value(record.get("arrival_time_min")),
            sqlite_value(record.get("start_time_min")), sqlite_value(record.get("completion_time_min")),
            sqlite_value(record.get("cycle_time_min")), sqlite_value(record.get("base_cycle_time_min")),
            sqlite_value(record.get("installation_time_min")), sqlite_value(record.get("ctd_min")),
            sqlite_value(record.get("queue_length")), sqlite_value(record.get("waiting_time_min")),
            sqlite_value(record.get("utilization_pct")), sqlite_value(record.get("station_status")),
            sqlite_value(record.get("equipment_health")), sqlite_value(record.get("maintenance_active")),
            sqlite_value(record.get("equipment_driven")), sqlite_value(record.get("health_slowdown_min")),
            sqlite_value(record.get("defect_present")), sqlite_value(record.get("defect_introduced_here")),
            sqlite_value(record.get("defect_detected")), sqlite_value(record.get("defect_cause")),
            sqlite_value(record.get("defect_type")), sqlite_value(record.get("defect_severity")),
            sqlite_value(record.get("defect_risk_score")), sqlite_value(record.get("defect_source_station")),
            sqlite_value(record.get("process_drift_score")), sqlite_value(record.get("input_variation_score")),
            sqlite_value(record.get("fixture_alignment_score")), sqlite_value(record.get("environmental_deviation_score")),
            json.dumps(sensor_data, ensure_ascii=False, separators=(",", ":")), created,
        )

    def write_records(self, records: Iterable[Dict[str, Any]]) -> int:
        records = [normalise_record(record) for record in records if record]
        if not records: return 0

        with self._lock:
            rows = [self._database_row(record) for record in records]
            with self._connect() as connection:
                connection.executemany(
                    """
                    INSERT INTO telemetry (
                        vehicle_id, station_id, station_name, station_family, simulation_time_hours,
                        arrival_time_min, start_time_min, completion_time_min, cycle_time_min,
                        base_cycle_time_min, installation_time_min, ctd_min, queue_length,
                        waiting_time_min, utilization_pct, station_status, equipment_health,
                        maintenance_active, equipment_driven, health_slowdown_min, defect_present,
                        defect_introduced_here, defect_detected, defect_cause, defect_type,
                        defect_severity, defect_risk_score, defect_source_station, process_drift_score,
                        input_variation_score, fixture_alignment_score, environmental_deviation_score,
                        sensor_data_json, record_created_utc
                    )
                    VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?
                    )
                    """,
                    rows,
                )
                connection.commit()

            self._append_csv(records)
            self._append_jsonl(records)
            self._records_written += len(records)
            return len(records)

    def consume_controller(self, controller: Any) -> int:
        if not hasattr(controller, "get_new_telemetry"):
            raise AttributeError("The Phase 6 controller must provide get_new_telemetry().")
        return self.write_records(controller.get_new_telemetry())

    def start_run(self) -> int:
        started = datetime.now(timezone.utc).isoformat()
        with self._lock:
            with self._connect() as connection:
                cursor = connection.execute("INSERT INTO simulation_runs (started_utc, status) VALUES (?, 'RUNNING')", (started,))
                connection.commit()
                return int(cursor.lastrowid)

    def finish_run(self, run_id: int, status: str = "COMPLETED") -> None:
        completed = datetime.now(timezone.utc).isoformat()
        with self._lock:
            with self._connect() as connection:
                connection.execute(
                    "UPDATE simulation_runs SET completed_utc = ?, records_written = ?, status = ? WHERE run_id = ?",
                    (completed, self._records_written, status, run_id)
                )
                connection.commit()

    def count_records(self) -> int:
        with self._connect() as connection:
            row = connection.execute("SELECT COUNT(*) FROM telemetry").fetchone()
            return int(row[0])

    def count_vehicles(self) -> int:
        with self._connect() as connection:
            row = connection.execute("SELECT COUNT(DISTINCT vehicle_id) FROM telemetry WHERE vehicle_id IS NOT NULL").fetchone()
            return int(row[0])

    def count_stations(self) -> int:
        with self._connect() as connection:
            row = connection.execute("SELECT COUNT(DISTINCT station_id) FROM telemetry WHERE station_id IS NOT NULL").fetchone()
            return int(row[0])

    def station_summary(self) -> List[Dict[str, Any]]:
        with self._connect() as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                """
                SELECT
                    station_id, station_name, station_family, COUNT(*) AS records,
                    AVG(cycle_time_min) AS avg_cycle_time_min, AVG(waiting_time_min) AS avg_waiting_time_min,
                    AVG(queue_length) AS avg_queue_length, AVG(utilization_pct) AS avg_utilization_pct,
                    AVG(equipment_health) AS avg_equipment_health
                FROM telemetry
                GROUP BY station_id, station_name, station_family
                ORDER BY station_id
                """
            ).fetchall()
            return [dict(row) for row in rows]

    def latest_records(self, limit: int = 20) -> List[Dict[str, Any]]:
        limit = max(1, int(limit))
        with self._connect() as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute("SELECT * FROM telemetry ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
            return [dict(row) for row in rows]

    def summary(self) -> Dict[str, Any]:
        return {
            "database": str(self.database_path),
            "csv": str(self.csv_path) if self.enable_csv else None,
            "jsonl": str(self.jsonl_path) if self.enable_jsonl else None,
            "records_written_this_session": self._records_written,
            "records_in_database": self.count_records(),
            "vehicles_in_database": self.count_vehicles(),
            "stations_in_database": self.count_stations(),
        }

def attach_to_controller(controller: Any, data_layer: TelemetryDataLayer) -> None:
    existing_callback = getattr(controller, "on_telemetry", None)
    def telemetry_callback(record: Dict[str, Any]) -> None:
        data_layer.write_records([record])
        if existing_callback: existing_callback(record)
    controller.on_telemetry = telemetry_callback