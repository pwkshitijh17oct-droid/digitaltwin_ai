from __future__ import annotations
import csv
import importlib.util
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "phase1_station_config.json"
PHASE3_PATH = BASE_DIR / "phase3_health_maintenance_engine.py"

REAL_YEAR_MINUTES = 365.0 * 24.0 * 60.0
TOL = 1e-9

DEFAULT_QUEUE_CAPACITY = 10
SPECIAL_QUEUE_CAPACITY = {"S10": 50, "S20": 50}

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

P3 = load_module("digitaltwin_phase4_phase3_runtime", PHASE3_PATH)

@dataclass
class Vehicle:
    vehicle_id: int
    release_time_min: float
    station_index: int = 0
    ready_time_min: float = 0.0
    queued: bool = False
    completed: bool = False

@dataclass
class StationRuntime:
    processing_vehicle_id: Optional[int] = None
    blocked_vehicle_id: Optional[int] = None
    busy_until_min: float = 0.0
    busy_time_min: float = 0.0
    vehicles_processed: int = 0
    total_waiting_time_min: float = 0.0
    total_queue_length: float = 0.0
    queue_observations: int = 0
    max_queue_length: int = 0
    running_count: int = 0
    blocked_count: int = 0
    starved_count: int = 0
    maintenance_count: int = 0
    recovery_start_count: int = 0
    recovery_vehicle_count: int = 0
    recovery_slack_used_min: float = 0.0
    recovery_completed_count: int = 0
    recovery_armed: bool = False
    recovery_active: bool = False

@dataclass
class VehicleStationEvent:
    vehicle_id: int
    station_id: str
    station_name: str
    station_family: str
    arrival_time_min: float
    start_time_min: float
    completion_time_min: float
    waiting_time_min: float
    base_cycle_time_min: float
    installation_time_min: float
    health_slowdown_min: float
    cycle_time_min: float
    ctd_min: float
    equipment_health: float
    queue_length: int
    queue_capacity: int
    takt_slack_min: float
    recovery_mode: bool
    recovery_trigger: str
    utilization_pct: float
    station_status: str
    maintenance_active: bool
    tool_replacement_event: bool
    tool_replacement_number: int

class IncrementalLineEngine:
    def __init__(self, config_path: str | Path = CONFIG_PATH, seed: int = 42,
                 line_takt_min: Optional[float] = None):
        self.config_path = Path(config_path)
        self.config = json.loads(self.config_path.read_text(encoding="utf-8"))
        self.stations = {s["id"]: s for s in self.config["stations"]}
        self.station_order = [s["id"] for s in self.config["stations"]]
        self.rng_seed = int(seed)
        self.health_engine = P3.HealthEngine(self.config_path, seed=self.rng_seed)
        self.line_takt_min = float(line_takt_min) if line_takt_min is not None else self._calculate_takt()
        self.reset()

    def _base_ct(self, station):
        return float(station.get("base_ct_min", 1.0))

    def _installation_time(self, station):
        params = station.get("parameters", {})
        value = params.get("installation_time", station.get("installation_time_min", 0.0))
        if isinstance(value, dict):
            value = value.get("target", 0.0)
        return max(0.0, float(value or 0.0))

    def _calculate_takt(self):
        values = [self._base_ct(s) + self._installation_time(s) for s in self.stations.values() if s.get("family") != "buffer"]
        return max(values) if values else 1.0

    def queue_capacity(self, station_id):
        if station_id in SPECIAL_QUEUE_CAPACITY:
            return SPECIAL_QUEUE_CAPACITY[station_id]
        value = self.stations[station_id].get("queue_capacity", DEFAULT_QUEUE_CAPACITY)
        try:
            return max(1, int(value))
        except (TypeError, ValueError):
            return DEFAULT_QUEUE_CAPACITY

    def _health(self, station_id, time_min):
        return float(self.health_engine.health_for_next_vehicle(station_id, self.runtime[station_id].vehicles_processed))

    def _actual_ct(self, station, health):
        base = self._base_ct(station)
        installation = self._installation_time(station)
        if station.get("family") == "buffer" or not bool(station.get("health_enabled", True)):
            return base + installation, installation, 0.0
        sensitivity = float(station.get("health_ct_sensitivity", 0.45))
        health = max(0.0, min(1.0, float(health)))
        if health >= 0.98:
            slowdown = 0.0
        else:
            degradation = max(0.0, min(1.0, (1.0 - health) / 0.30))
            slowdown = base * sensitivity * degradation * degradation
        slowdown = min(slowdown, base * 0.60)
        return base + installation + slowdown, installation, slowdown

    def reset(self):
        self.current_time_min = 0.0
        self.next_vehicle_id = 1
        self.total_released_vehicles = 0
        self.total_completed_vehicles = 0
        self.vehicles = {}
        self.queues = {sid: [] for sid in self.station_order}
        self.runtime = {sid: StationRuntime() for sid in self.station_order}
        self.events = []
        self._new_events = []
        self.operator_events = []
        self._pending_replacement_event = {}
        self.status = "READY"
        self.health_engine = P3.HealthEngine(self.config_path, seed=self.rng_seed)

    def operator_health_reset(self, station_id):
        rt = self.runtime[station_id]
        result = self.health_engine.reset_health(
            station_id, self.current_time_min / REAL_YEAR_MINUTES, "OPERATOR_HT", 0.98, rt.vehicles_processed
        )
        self._pending_replacement_event[station_id] = dict(result)
        self.operator_events.append(dict(result))
        return result

    def _release_until(self, target_min):
        first = self.station_order[0]
        cap = self.queue_capacity(first)
        while True:
            release_time = (self.next_vehicle_id - 1) * self.line_takt_min
            if release_time > target_min + TOL:
                break
            if len(self.queues[first]) >= cap:
                break
            vid = self.next_vehicle_id
            self.next_vehicle_id += 1
            self.total_released_vehicles += 1
            v = Vehicle(vid, release_time, 0, release_time, True, False)
            self.vehicles[vid] = v
            self.queues[first].append(vid)

    def _try_start(self, station_index):
        sid = self.station_order[station_index]
        station = self.stations[sid]
        rt = self.runtime[sid]
        q = self.queues[sid]
        
        if rt.processing_vehicle_id is not None or rt.blocked_vehicle_id is not None or rt.busy_until_min > self.current_time_min + TOL:
            return None
            
        if not q:
            return None

        vehicle_id = q.pop(0)
        vehicle = self.vehicles[vehicle_id]
        vehicle.queued = False
        arrival = float(vehicle.ready_time_min)
        start = max(self.current_time_min, arrival)
        
        waiting = max(0.0, start - arrival)
        health = self._health(sid, start)
        actual_ct, installation, slowdown = self._actual_ct(station, health)
        completion = start + actual_ct
        slack = max(0.0, self.line_takt_min - actual_ct)
        queue_after_start = len(q)

        replacement = self._pending_replacement_event.pop(sid, None)
        if replacement is not None:
            health_before = float(replacement.get("health_before", 1.0))
            health_after = float(replacement.get("health_after", 0.0))
            if health_before <= 0.70 + 1e-6 and health_after >= 0.90 - 1e-6:
                if queue_after_start > 0:
                    rt.recovery_armed = True
                    rt.recovery_active = False
                else:
                    rt.recovery_armed = False

        recovery_mode = False
        recovery_trigger = "NONE"
        if rt.recovery_armed:
            if actual_ct < self.line_takt_min - TOL:
                recovery_mode = True
                recovery_trigger = "HEALTH_RESTORATION_RECOVERY"

        if recovery_mode:
            if not rt.recovery_active:
                rt.recovery_start_count += 1
                rt.recovery_active = True
            rt.recovery_vehicle_count += 1
            rt.recovery_slack_used_min += slack
            if queue_after_start == 0:
                rt.recovery_completed_count += 1
                rt.recovery_armed = False
                rt.recovery_active = False

        status = "RECOVERY" if recovery_mode else ("BLOCKED" if waiting > TOL else "RUNNING")
        rt.processing_vehicle_id = vehicle_id
        rt.busy_until_min = completion
        rt.busy_time_min += actual_ct
        rt.vehicles_processed += 1
        rt.total_waiting_time_min += waiting
        rt.total_queue_length += queue_after_start
        rt.queue_observations += 1
        rt.max_queue_length = max(rt.max_queue_length, queue_after_start)
        
        if status == "BLOCKED":
            rt.blocked_count += 1
        else:
            rt.running_count += 1

        util = min(100.0, rt.busy_time_min / max(completion, 1e-9) * 100.0)
        event = VehicleStationEvent(
            vehicle_id=vehicle_id, station_id=sid, station_name=station["name"], station_family=station["family"],
            arrival_time_min=round(arrival, 3), start_time_min=round(start, 3), completion_time_min=round(completion, 3),
            waiting_time_min=round(waiting, 3), base_cycle_time_min=round(self._base_ct(station), 3),
            installation_time_min=round(installation, 3), health_slowdown_min=round(slowdown, 3),
            cycle_time_min=round(actual_ct, 3), ctd_min=round(max(0.0, completion - arrival), 3),
            equipment_health=round(health, 3), queue_length=queue_after_start, queue_capacity=self.queue_capacity(sid),
            takt_slack_min=round(slack, 3), recovery_mode=bool(recovery_mode), recovery_trigger=recovery_trigger,
            utilization_pct=round(util, 3), station_status=status, maintenance_active=False,
            tool_replacement_event=replacement is not None, tool_replacement_number=int((replacement or {}).get("tool_replacement_number", 0))
        )
        self.events.append(event)
        self._new_events.append(event)
        return completion

    def _complete_transfers(self):
        changed = False
        for i in range(len(self.station_order) - 1, -1, -1):
            sid = self.station_order[i]
            rt = self.runtime[sid]
            
            if rt.blocked_vehicle_id is not None:
                downstream = self.station_order[i+1]
                dq = self.queues[downstream]
                if len(dq) < self.queue_capacity(downstream):
                    v = self.vehicles[rt.blocked_vehicle_id]
                    v.station_index = i + 1
                    v.ready_time_min = self.current_time_min
                    v.queued = True
                    dq.append(v.vehicle_id)
                    rt.blocked_vehicle_id = None
                    changed = True
                    
            vid = rt.processing_vehicle_id
            if vid is not None and rt.busy_until_min <= self.current_time_min + TOL:
                if i == len(self.station_order) - 1:
                    v = self.vehicles[vid]
                    v.completed = True
                    v.station_index = len(self.station_order)
                    v.queued = False
                    self.total_completed_vehicles += 1
                    rt.processing_vehicle_id = None
                    rt.busy_until_min = 0.0
                    changed = True
                else:
                    downstream = self.station_order[i+1]
                    dq = self.queues[downstream]
                    if len(dq) < self.queue_capacity(downstream):
                        v = self.vehicles[vid]
                        v.station_index = i + 1
                        v.ready_time_min = self.current_time_min
                        v.queued = True
                        dq.append(v.vehicle_id)
                        rt.processing_vehicle_id = None
                        rt.busy_until_min = 0.0
                        changed = True
                    else:
                        rt.blocked_vehicle_id = vid
                        rt.processing_vehicle_id = None
                        rt.blocked_count += 1
                        changed = True

        for sid in self.station_order:
            rt = self.runtime[sid]
            if rt.vehicles_processed > 0 and self.health_engine.replacement_due(sid, rt.vehicles_processed):
                if sid not in self._pending_replacement_event:
                    self._pending_replacement_event[sid] = self.health_engine.record_automatic_replacement(
                        sid, self.current_time_min / REAL_YEAR_MINUTES, rt.vehicles_processed
                    )
                    rt.recovery_armed = False
                    rt.recovery_active = False
                    changed = True
        return changed

    def _next_event_time(self, target_min):
        next_time = target_min
        next_release = (self.next_vehicle_id - 1) * self.line_takt_min
        if self.current_time_min + TOL < next_release < next_time - TOL:
            next_time = next_release
        for rt in self.runtime.values():
            if self.current_time_min + TOL < rt.busy_until_min < next_time - TOL:
                next_time = rt.busy_until_min
        return next_time

    def _progress_current_time(self):
        changed = False
        self._release_until(self.current_time_min)
        if self._complete_transfers(): changed = True
        for _ in range(len(self.station_order) * 2 + 4):
            local = False
            for i in range(len(self.station_order)):
                if self._try_start(i) is not None:
                    local = True; changed = True
            if self._complete_transfers():
                local = True; changed = True
            if not local: break
        return changed

    def step(self, minutes):
        if minutes < 0: raise ValueError("minutes must be >= 0")
        
        target = self.current_time_min + float(minutes)
        self._new_events.clear()
        
        while self.current_time_min < target - TOL:
            self._progress_current_time()
            next_time = self._next_event_time(target)
            if next_time <= self.current_time_min + TOL:
                next_time = target
            self.current_time_min = min(next_time, target)
            
        self._progress_current_time()
        self.status = "RUNNING"
        return self.get_state()

    def get_new_events(self):
        rows = [asdict(e) for e in self._new_events]
        self._new_events.clear()
        return rows

    def get_all_events(self):
        return [asdict(e) for e in self.events]

    def _station_state(self, sid):
        s = self.stations[sid]
        rt = self.runtime[sid]
        q = self.queues[sid]
        health = self._health(sid, self.current_time_min)
        actual, install, slowdown = self._actual_ct(s, health)
        slack = max(0.0, self.line_takt_min - actual)
        recovery = (rt.recovery_armed and len(q) > 0 and actual < self.line_takt_min - TOL)
        
        if rt.blocked_vehicle_id is not None:
            status = "BLOCKED"
        elif recovery:
            status = "RECOVERY"
        elif rt.processing_vehicle_id is not None or q:
            status = "RUNNING"
        else:
            status = "STARVED"

        return {
            "station_id": sid, "station_name": s["name"], "family": s["family"],
            "base_cycle_time_min": round(self._base_ct(s), 3), "installation_time_min": round(install, 3),
            "current_cycle_time_min": round(actual, 3), "health_slowdown_min": round(slowdown, 3),
            "line_takt_min": round(self.line_takt_min, 3), "takt_slack_min": round(slack, 3),
            "equipment_health": round(health, 3), "station_status": status, "recovery_mode": bool(recovery),
            "recovery_trigger": "HEALTH_RESTORATION_RECOVERY" if recovery else "NONE",
            "queue_length": len(q), "queue_capacity": self.queue_capacity(sid), "queue_full": len(q) >= self.queue_capacity(sid),
            "processing_vehicle_id": rt.processing_vehicle_id, "blocked_vehicle_id": rt.blocked_vehicle_id,
            "busy_until_min": round(rt.busy_until_min, 3), "vehicles_processed": rt.vehicles_processed,
            "tool_life_vehicles": self.health_engine.tool_life(sid),
            "vehicles_since_last_replacement": max(0, rt.vehicles_processed - self.health_engine.last_replacement_processed.get(sid, 0)),
            "automatic_replacement_count": self.health_engine.auto_replacement_count.get(sid, 0),
            "manual_replacement_count": self.health_engine.manual_replacement_count.get(sid, 0),
            "recovery_armed": bool(rt.recovery_armed), "recovery_start_count": rt.recovery_start_count,
            "recovery_vehicle_count": rt.recovery_vehicle_count, "recovery_slack_used_min": round(rt.recovery_slack_used_min, 3),
            "recovery_completed_count": rt.recovery_completed_count, "max_queue_length": rt.max_queue_length,
            "average_waiting_time_min": round(rt.total_waiting_time_min / max(rt.vehicles_processed, 1), 3),
        }

    def get_state(self):
        active = [{"vehicle_id": v.vehicle_id, "release_time_min": round(v.release_time_min, 3), "station_id": self.station_order[v.station_index] if 0 <= v.station_index < len(self.station_order) else None, "station_index": v.station_index, "ready_time_min": round(v.ready_time_min, 3), "queued": v.queued} for v in self.vehicles.values() if not v.completed]
        return {
            "status": self.status, "simulation_time_hours": round(self.current_time_min / REAL_YEAR_MINUTES, 8),
            "production_time_min": round(self.current_time_min, 3), "real_year_fraction": round(self.current_time_min / REAL_YEAR_MINUTES, 8),
            "line_takt_min": round(self.line_takt_min, 3), "station_count": len(self.station_order),
            "next_vehicle_id": self.next_vehicle_id, "total_released_vehicles": self.total_released_vehicles,
            "total_completed_vehicles": self.total_completed_vehicles, "active_vehicle_count": len(active),
            "stations": {sid: self._station_state(sid) for sid in self.station_order}, "active_vehicles": active,
            "operator_health_resets": len(self.operator_events),
        }