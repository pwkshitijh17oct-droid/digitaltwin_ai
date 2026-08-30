from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

REAL_YEAR_MINUTES = 365.0 * 24.0 * 60.0
SIM_YEAR_HOURS = 1.0
HEALTH_THRESHOLD = 0.700
DEFAULT_TOOL_LIFE_VEHICLES = 330
DEFAULT_RECOVERY_HEALTH = 0.980

@dataclass
class MaintenanceEvent:
    station_id: str
    event_number: int
    start_time_hours: float
    duration_hours: float
    end_time_hours: float
    health_before: float
    health_after: float
    recovery_fraction: float
    maintenance_type: str
    maintenance_action: str
    tool_replacement_event: bool = True
    tool_replacement_number: int = 0
    trigger: str = "VEHICLE_TOOL_LIFE"

    def to_dict(self):
        return {
            "station_id": self.station_id,
            "event_number": self.event_number,
            "start_time_hours": round(self.start_time_hours, 6),
            "duration_hours": round(self.duration_hours, 6),
            "end_time_hours": round(self.end_time_hours, 6),
            "health_before": round(self.health_before, 3),
            "health_after": round(self.health_after, 3),
            "recovery_fraction": round(self.recovery_fraction, 6),
            "maintenance_type": self.maintenance_type,
            "maintenance_action": self.maintenance_action,
            "tool_replacement_event": self.tool_replacement_event,
            "tool_replacement_number": self.tool_replacement_number,
            "trigger": self.trigger,
        }

class HealthEngine:
    """Vehicle-count based equipment health and tool replacement engine."""

    def __init__(self, config_path: str | Path, seed: Optional[int] = 42):
        self.config_path = Path(config_path)
        self.config = json.loads(self.config_path.read_text(encoding="utf-8"))
        self.stations = {s["id"]: s for s in self.config["stations"]}
        self.seed = seed
        self.manual_resets: Dict[str, List[Dict[str, Any]]] = {}
        self.manual_replacement_count: Dict[str, int] = {}
        self.auto_replacement_count: Dict[str, int] = {}
        self._last_auto_age: Dict[str, int] = {}
        self._replacement_events: Dict[str, List[MaintenanceEvent]] = {}
        
        self.last_replacement_processed: Dict[str, int] = {sid: 0 for sid in self.stations}
        
        # UPDATED: Pull initial_health from configuration instead of defaulting to 1.0
        self.last_replacement_health: Dict[str, float] = {
            sid: float(s.get("maintenance", {}).get("initial_health", 1.0))
            for sid, s in self.stations.items()
        }

    def _station(self, sid): 
        if sid not in self.stations: raise KeyError(f"Unknown station: {sid}")
        return self.stations[sid]

    def _enabled(self, sid):
        s = self._station(sid)
        return sid not in {"S10","S20"} and bool(s.get("health_enabled", True))

    def _cfg(self, sid):
        return self._station(sid).get("maintenance", {})

    def tool_life(self, sid):
        cfg = self._cfg(sid)
        value = cfg.get("tool_life_vehicles", DEFAULT_TOOL_LIFE_VEHICLES)
        try: return max(1, int(value))
        except (TypeError, ValueError): return DEFAULT_TOOL_LIFE_VEHICLES

    def threshold(self, sid):
        try: return float(self._cfg(sid).get("maintenance_threshold", HEALTH_THRESHOLD))
        except (TypeError, ValueError): return HEALTH_THRESHOLD

    def recovery_health(self, sid):
        try: return max(self.threshold(sid), min(1.0, float(self._cfg(sid).get("recovery_health", DEFAULT_RECOVERY_HEALTH))))
        except (TypeError, ValueError): return DEFAULT_RECOVERY_HEALTH

    def health_from_age(self, sid, age: int, start_health: float = 1.0):
        if not self._enabled(sid): return 1.0
        L = self.tool_life(sid)
        th = self.threshold(sid)
        age = max(0, min(L, int(age)))
        start = max(th, min(1.0, float(start_health)))
        return max(th, start - (start - th) * (age / L) ** 2)

    def get_health(self, station_id: str, time_hours: float, vehicles_processed: Optional[int] = None) -> float:
        self._station(station_id)
        if not self._enabled(station_id): return 1.0
        if vehicles_processed is None:
            vehicles_processed = 0
        return round(self.get_health_by_vehicle_count(station_id, int(vehicles_processed)), 6)

    def get_health_by_vehicle_count(self, station_id: str, vehicles_processed: int) -> float:
        if not self._enabled(station_id):
            return 1.0
        processed = max(0, int(vehicles_processed))
        reset_at = self.last_replacement_processed.get(station_id, 0)
        age = max(0, processed - reset_at)
        start_health = self.last_replacement_health.get(station_id, 1.0)

        manual = self.manual_resets.get(station_id, [])
        if manual:
            latest = max(manual, key=lambda x: x["vehicles_processed"])
            if int(latest["vehicles_processed"]) >= reset_at and int(latest["vehicles_processed"]) <= processed:
                reset_at = int(latest["vehicles_processed"])
                age = processed - reset_at
                start_health = float(latest["health_after"])

        return round(self.health_from_age(station_id, age, start_health), 6)

    def health_for_next_vehicle(self, station_id: str, vehicles_processed: int) -> float:
        if not self._enabled(station_id):
            return 1.0
        processed = max(0, int(vehicles_processed))
        reset_at = self.last_replacement_processed.get(station_id, 0)
        start_health = self.last_replacement_health.get(station_id, 1.0)
        
        manual = self.manual_resets.get(station_id, [])
        if manual:
            latest = max(manual, key=lambda x: x["vehicles_processed"])
            if int(latest["vehicles_processed"]) >= reset_at and int(latest["vehicles_processed"]) <= processed:
                reset_at = int(latest["vehicles_processed"])
                start_health = float(latest["health_after"])
                
        age = max(0, processed - reset_at)
        if age == 0:
            return round(start_health, 6)
        return round(self.health_from_age(station_id, min(self.tool_life(station_id), age + 1), start_health), 6)

    def replacement_due(self, station_id: str, vehicles_processed: int) -> bool:
        if not self._enabled(station_id):
            return False
        processed = max(0, int(vehicles_processed))
        reset_at = self.last_replacement_processed.get(station_id, 0)
        return processed > reset_at and (processed - reset_at) >= self.tool_life(station_id)

    def record_automatic_replacement(self, station_id: str, time_hours: float, vehicles_processed: int) -> Dict[str, Any]:
        if not self._enabled(station_id):
            return {"station_id": station_id, "tool_replacement_event": False, "tool_replacement_number": 0}
        
        # Calculate health precisely at the end of tool life for telemetry
        before = self.health_from_age(station_id, self.tool_life(station_id), self.last_replacement_health.get(station_id, 1.0))
        
        n = self.auto_replacement_count.get(station_id, 0) + 1
        self.auto_replacement_count[station_id] = n
        after = self.recovery_health(station_id)
        
        self.last_replacement_processed[station_id] = int(vehicles_processed)
        self.last_replacement_health[station_id] = after
        
        event = {
            "station_id": station_id,
            "time_hours": round(float(time_hours), 6),
            "vehicles_processed": int(vehicles_processed),
            "health_before": round(before, 3),
            "health_after": round(after, 3),
            "event_type": "AUTOMATIC_TOOL_REPLACEMENT",
            "reason": "TOOL_LIFE_REACHED",
            "maintenance_type": "TOOL_REPLACEMENT",
            "maintenance_action": "AUTOMATIC_TOOL_REPLACEMENT",
            "tool_replacement_event": True,
            "tool_replacement_number": n,
            "trigger": "VEHICLE_TOOL_LIFE",
        }
        self._replacement_events.setdefault(station_id, []).append(
            MaintenanceEvent(
                station_id, n, float(time_hours), 0.0, float(time_hours),
                before, after, after, "TOOL_REPLACEMENT",
                "AUTOMATIC_TOOL_REPLACEMENT", True, n, "VEHICLE_TOOL_LIFE"
            )
        )
        return event

    def reset_health(self, station_id, time_hours, reason="OPERATOR_HT", recovery_health=DEFAULT_RECOVERY_HEALTH, vehicles_processed=0):
        self._station(station_id)
        if not self._enabled(station_id):
            return {"station_id": station_id, "time_hours": round(float(time_hours),6), "health_before":1.0, "health_after":1.0,
                    "event_type":"IGNORED","reason":"Buffer station has no equipment health.","tool_replacement_event":False,"tool_replacement_number":0}
                    
        before = self.get_health_by_vehicle_count(station_id, vehicles_processed)
        count = self.manual_replacement_count.get(station_id, 0) + 1
        self.manual_replacement_count[station_id] = count
        
        self.last_replacement_processed[station_id] = int(vehicles_processed)
        self.last_replacement_health[station_id] = max(self.threshold(station_id), min(1.0, float(recovery_health)))
        recovery = max(self.threshold(station_id), min(1.0, float(recovery_health)))
        
        event = {
            "station_id": station_id, "time_hours": round(float(time_hours),6),
            "vehicles_processed": int(vehicles_processed),
            "health_before": round(before,3), "health_after": round(recovery,3),
            "event_type":"OPERATOR_HEALTH_RESET","reason":reason,
            "maintenance_type":"TOOL_REPLACEMENT","maintenance_action":"OPERATOR_TOOL_REPLACEMENT",
            "tool_replacement_event":True,"tool_replacement_number":count,"trigger":"OPERATOR",
        }
        self.manual_resets.setdefault(station_id, []).append({
            "vehicles_processed": int(vehicles_processed),
            "time_hours": float(time_hours),
            "health_after": recovery,
            "event": dict(event),
        })
        return event

    def get_maintenance_events(self, station_id):
        return list(self._replacement_events.get(station_id, []))

    def get_station_state(self, station_id, time_hours, vehicles_processed: int = 0):
        health = self.get_health_by_vehicle_count(station_id, vehicles_processed)
        return {
            "station_id": station_id,
            "time_hours": round(float(time_hours),6),
            "equipment_health": round(health,3),
            "maintenance_count": len(self._replacement_events.get(station_id, [])),
            "in_maintenance": False,
            "maintenance_event_number": None,
            "maintenance_action": None,
            "tool_replacement_event": False,
            "tool_replacement_number": 0,
            "manual_reset_count": len(self.manual_resets.get(station_id, [])),
            "latest_manual_reset": self.manual_resets.get(station_id, [])[-1] if self.manual_resets.get(station_id) else None,
        }

    def generate_all_schedules(self):
        return {sid:[e.to_dict() for e in self.get_maintenance_events(sid)] for sid in self.stations}