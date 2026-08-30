"""
DIGITALTWIN.AI
PHASE 6 - LIVE SIMULATION CONTROLLER
"""

from __future__ import annotations

import importlib.util
import json
import signal
import sys
import threading
import time
import queue
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


BASE_DIR = Path(__file__).resolve().parent

LIVE_DATA_DIR = BASE_DIR / "live simulation data"
LIVE_DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_module(module_name: str, path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Required module not found: {path}")
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

def next_generation_number() -> int:
    numbers = []
    for path in LIVE_DATA_DIR.iterdir():
        if not path.is_dir(): continue
        name = path.name.lower()
        if not name.startswith("generation"): continue
        suffix = name.replace("generation", "", 1)
        if suffix.isdigit(): numbers.append(int(suffix))
    return max(numbers) + 1 if numbers else 1

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

class IntegratedSimulationController:

    def __init__(
        self,
        speed: float = 8760.0,
        max_telemetry_records: int = 10000,
        seed: int = 42,
        enable_phase7: bool = True,
    ):
        self.p4 = load_module("dt_live_p4", BASE_DIR / "phase4_incremental_line_engine.py")
        self.p2 = load_module("dt_live_p2", BASE_DIR / "phase2_sensor_engine.py")
        self.p5 = load_module("dt_live_p5", BASE_DIR / "phase5_telemetry_generator.py")
        self.p7 = load_module("dt_live_p7", BASE_DIR / "phase7_data_layer.py")
        self.pd = load_module("dt_live_defect", BASE_DIR / "defect_model.py")

        self.config_path = BASE_DIR / "phase1_station_config.json"
        self.config = json.loads(self.config_path.read_text(encoding="utf-8"))

        self.seed = int(seed)
        self.engine = self.p4.IncrementalLineEngine(self.config_path, seed=self.seed)
        self.sensor = self.p2.SensorEngine(self.config_path, seed=self.seed)
        self.defect = self.pd.DefectEngine(self.config_path, seed=self.seed)

        self.speed = float(speed)
        self.max_records = int(max_telemetry_records)

        self.telemetry: List[Dict[str, Any]] = []
        self.new: List[Dict[str, Any]] = []

        self.status = "READY"
        self.lock = threading.RLock()
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.thread: Optional[threading.Thread] = None
        self.enable_phase7 = bool(enable_phase7)

        self.generation_number: Optional[int] = None
        self.generation_dir: Optional[Path] = None
        self.data_layer = None
        self.run_id = None
        self.generation_started_utc = None
        self.generation_finished_utc = None
        self.generation_records_written = 0
        self.generation_status = "NOT_STARTED"
        self._closed = False

    def _create_generation(self) -> None:
        if self.generation_number is not None:
            raise RuntimeError("A generation already exists.")

        generation_number = next_generation_number()
        generation_dir = LIVE_DATA_DIR / f"generation{generation_number}"
        generation_dir.mkdir(parents=True, exist_ok=False)

        self.generation_number = generation_number
        self.generation_dir = generation_dir
        self.generation_started_utc = utc_now()
        self.generation_finished_utc = None
        self.generation_records_written = 0
        self.generation_status = "RUNNING"

        if self.enable_phase7:
            self.data_layer = self.p7.TelemetryDataLayer(
                database_path=(generation_dir / "digitaltwin_telemetry.db"),
                csv_path=(generation_dir / "telemetry.csv"),
                jsonl_path=(generation_dir / "telemetry.jsonl"),
                enable_csv=True,
                enable_jsonl=True,
            )
            self.run_id = self.data_layer.start_run()

        self._write_generation_metadata()

    def _write_generation_metadata(self, final: bool = False) -> None:
        if self.generation_dir is None:
            return
        payload = {
            "generation": self.generation_number,
            "status": self.generation_status,
            "started_utc": self.generation_started_utc,
            "finished_utc": self.generation_finished_utc,
            "records_written": self.generation_records_written,
            "simulation_time_hours": round(self.engine.current_time_min / (365 * 24 * 60), 8),
            "production_time_min": round(self.engine.current_time_min, 3),
            "total_released_vehicles": self.engine.total_released_vehicles,
            "total_completed_vehicles": self.engine.total_completed_vehicles,
            "files": {
                "sqlite": str(self.generation_dir / "digitaltwin_telemetry.db"),
                "csv": str(self.generation_dir / "telemetry.csv"),
                "jsonl": str(self.generation_dir / "telemetry.jsonl"),
            },
        }
        path = self.generation_dir / "generation_summary.json"
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _finish_generation(self, status: str) -> None:
        if self.generation_number is None:
            return
        self.generation_status = status
        self.generation_finished_utc = utc_now()

        if self.data_layer is not None and self.run_id is not None:
            self.data_layer.finish_run(self.run_id, status=status)

        self._write_generation_metadata(final=True)
        self.data_layer = None
        self.run_id = None

    def _station_meta(self) -> Dict[str, Dict[str, Any]]:
        return {
            s["id"]: {
                "station_id": s["id"], "station_name": s["name"], "station_family": s["family"],
                "equipment_driven": s.get("equipment_driven", False),
            } for s in self.config["stations"]
        }

    def _publish(self, events: List[Dict[str, Any]]) -> None:
        if not events: return
        event_rows = []
        sensor_rows = []

        for event in events:
            event_row = dict(event)
            event_row["simulation_time_hours"] = round(event["completion_time_min"] / (365 * 24 * 60), 8)
            sensor = self.sensor.generate_station_reading(event["station_id"], event["equipment_health"], 1.0)
            defect = self.defect.evaluate(event["vehicle_id"], event["station_id"], sensor, event["equipment_health"])

            event_row.update(defect)
            sensor.update({"vehicle_id": event["vehicle_id"], "simulation_time_hours": event_row["simulation_time_hours"]})
            event_rows.append(event_row)
            sensor_rows.append(sensor)

        rows = self.p5.build_telemetry(event_rows, sensor_rows, self._station_meta())
        rows = [self._round(record) for record in rows]
        
        self.telemetry.extend(rows)
        self.new.extend(rows)

        if self.max_records and len(self.telemetry) > self.max_records:
            self.telemetry = self.telemetry[-self.max_records:]

        if self.data_layer is not None:
            written = self.data_layer.write_records(rows)
            self.generation_records_written += written
            self._write_generation_metadata()

    @staticmethod
    def _round(record: Dict[str, Any]) -> Dict[str, Any]:
        output = {}
        for key, value in record.items():
            if isinstance(value, (float, int)) and not isinstance(value, bool):
                if key == "simulation_time_hours":
                    output[key] = round(float(value), 8)
                else:
                    output[key] = round(float(value), 3)
            else:
                output[key] = value
        return output

    def start(self):
        with self.lock:
            if self.status != "READY": return self.get_state()
            self._create_generation()
            self.status = "RUNNING"
            self.stop_event.clear()
            self.pause_event.set()
            self._ensure_thread()
            return self.get_state()

    def pause(self):
        with self.lock:
            if self.status != "RUNNING": return self.get_state()
            self.status = "PAUSED"
            self.pause_event.clear() 
            self._write_generation_metadata()
            return self.get_state()

    def resume(self):
        with self.lock:
            if self.status != "PAUSED": return self.get_state()
            self.status = "RUNNING"
            self.stop_event.clear()
            self.pause_event.set()
            self._ensure_thread()
            self._write_generation_metadata()
            return self.get_state()

    def reset(self):
        with self.lock:
            if self.status == "READY": return self.get_state()
            self.stop_event.set()
            self.pause_event.clear()
            
            if self.thread is not None and self.thread.is_alive() and self.thread is not threading.current_thread():
                self.thread.join(timeout=2.0)
            self.thread = None

            self._finish_generation("RESET")
            self.engine.reset()
            self.sensor = self.p2.SensorEngine(self.config_path, seed=self.seed)
            self.defect = self.pd.DefectEngine(self.config_path, seed=self.seed)
            self.telemetry.clear()
            self.new.clear()
            
            self.generation_number = None
            self.generation_dir = None
            self.generation_started_utc = None
            self.generation_finished_utc = None
            self.generation_records_written = 0
            self.generation_status = "NOT_STARTED"
            self.status = "READY"
            return self.get_state()

    def _ensure_thread(self):
        if self.thread is not None and self.thread.is_alive(): return
        self.thread = threading.Thread(target=self._loop, name="DigitalTwinSimulation", daemon=True)
        self.thread.start()

    def _loop(self):
        previous_wall = time.monotonic()
        while not self.stop_event.is_set():
            if not self.pause_event.wait(timeout=0.05):
                previous_wall = time.monotonic() 
                continue

            now = time.monotonic()
            elapsed_wall = max(0.0, now - previous_wall)
            previous_wall = now

            with self.lock:
                if self.status != "RUNNING": continue
                production_minutes = elapsed_wall * self.speed / 60.0
                if production_minutes <= 0: continue
                self.engine.step(production_minutes)
                events = self.engine.get_new_events()
                self._publish(events)
            time.sleep(0.02)

    def operator_health_reset(self, station_id: str):
        with self.lock:
            if self.status not in ("RUNNING", "PAUSED"):
                return {"status": "IGNORED", "reason": "Simulation must be running or paused."}
            return self.engine.operator_health_reset(station_id)

    def get_state(self):
        state = self.engine.get_state()
        state.update({
            "controller_status": self.status,
            "generation": self.generation_number,
            "generation_records_written": self.generation_records_written,
        })
        return state

    def close(self, interrupted: bool = False):
        with self.lock:
            if self._closed: return
            self._closed = True
            self.stop_event.set()
            self.pause_event.clear()
            if self.thread is not None and self.thread.is_alive() and self.thread is not threading.current_thread():
                self.thread.join(timeout=2.0)
            if self.generation_number is not None:
                self._finish_generation("INTERRUPTED" if interrupted else "STOPPED")
            self.thread = None


def live_terminal():
    import random

    dynamic_seed = random.randint(1, 999999999)  # Generate a new seed every run

    controller = IntegratedSimulationController(
        speed=8760.0,
        max_telemetry_records=10000,
        seed=dynamic_seed,
        enable_phase7=True,
    )

    interrupted = False

    def handle_sigint(signum, frame):
        nonlocal interrupted
        interrupted = True
        print("\n\nCtrl+C received. Stopping safely...")
        controller.close(interrupted=True)

    signal.signal(signal.SIGINT, handle_sigint)

    print("\nDIGITALTWIN.AI - LIVE SIMULATOR")
    print("=" * 70)
    print("Commands (Type and press ENTER):")
    print("  S       Start new generation")
    print("  P       Pause simulation perfectly")
    print("  R       Resume current generation")
    print("  X       Reset and finalize generation")
    print("  HT Sxx  Operator health reset (e.g. HT S13)")
    print("  Q       Quit\n")

    cmd_queue = queue.Queue()

    def listen_for_input():
        while True:
            try:
                cmd = input()
                cmd_queue.put(cmd)
            except EOFError:
                cmd_queue.put("Q")
                break
            except Exception:
                break

    input_thread = threading.Thread(target=listen_for_input, daemon=True)
    input_thread.start()

    try:
        while not interrupted:
            state = controller.get_state()
            sim_days = state['production_time_min'] / (24.0 * 60.0)

            print(
                f"\r[{state['controller_status']}] "
                f"gen={state['generation']} | "
                f"time={sim_days:.2f} days | "
                f"released={state['total_released_vehicles']} | "
                f"completed={state['total_completed_vehicles']} | "
                f"records={state['generation_records_written']}      ",
                end="",
                flush=True,
            )

            try:
                command = cmd_queue.get(timeout=0.25).strip()
            except queue.Empty:
                continue

            command_upper = command.upper()
            if command_upper: print() 

            if command_upper in ("S", "START"):
                controller.start()
            elif command_upper in ("P", "PAUSE", "STOP"):
                controller.pause()
            elif command_upper in ("R", "RESUME"):
                controller.resume()
            elif command_upper in ("X", "RESET"):
                controller.reset()
            elif command_upper.startswith("HT "):
                parts = command_upper.split()
                if len(parts) == 2:
                    result = controller.operator_health_reset(parts[1])
                    print(f"Health reset applied: {result}")
            elif command_upper in ("Q", "QUIT", "EXIT"):
                break

    except KeyboardInterrupt:
        interrupted = True
        print("\n\nCtrl+C received.")
    finally:
        controller.close(interrupted=interrupted)
        print("\nController stopped.")

if __name__ == "__main__":
    live_terminal()