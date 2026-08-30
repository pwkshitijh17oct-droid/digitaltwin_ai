"""
DigitalTwin.ai -
Virtual Assembly Line Simulator
Sensor Generation Engine

Purpose
-------
Generate realistic process-sensor readings from the  station configuration.

this engine intentionally does NOT implement:
- vehicle movement
- queue calculations
- utilization
- equipment-health degradation
- maintenance
- ML
- dashboards

Those will be connected in later phases.

Core principle
--------------
A sensor is never generated as an unrestricted random number.

Depending on its type, a reading is generated using one of:
1. Stable process model
2. Drifting process model
3. Dependent process model
4. Derived measurement model
5. Equipment-health-adjusted model

For this engine, equipment health can optionally be supplied by a future health engine. 
If health is not supplied, the sensor engine assumes health = 1.0.

The engine maintains previous readings so consecutive values have temporal continuity 
instead of jumping independently.
"""

from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, Any

# Paths

DEFAULT_CONFIG_PATH = (
    Path(__file__).resolve().parent / "Station_config.json"
)

# Sensor classification

STABLE_SENSORS = {
    "ph",
    "bath_temperature",
    "oven_temperature",
    "airflow",
    "humidity",
    "paint_pressure",
    "pressure",
    "water_pressure",
    "conveyor_speed",
    "line_pressure",
    "adhesive_temperature",
    "weld_current",
    "weld_time",
    "voltage",
    "current",
    "brake_force",
    "wheel_speed",
    "test_time",
    "validation_time",
    "routing_time",
    "connector_force",
    "installation_force",
}

EQUIPMENT_HEALTH_SENSORS = {
    "equipment_vibration",
}

# Sensors that are conceptually dependent on another process variable.
# The actual dependency calculation is implemented below.
DEPENDENT_SENSORS = {
    "paint_flow",
    "flow_rate",
    "seal_thickness",
    "cure_time",
    "fill_time",
    "fluid_level",
    "adhesive_flow",
    "torque_angle",
    "gap",
    "temperature",
}

# Measurements that should be derived from an underlying value rather
# than independently generated in a later phase.
DERIVED_SENSORS = {
    "measurement_error",
    "occupancy",
    "inspection_score",
    "alignment_error",
    "ctd",
}

# Sensors that represent discrete/count outcomes.
DISCRETE_SENSORS = {
    "burr_count",
    "defect_count",
    "obd_error_count",
}

# Process/environment sensors for which slow temporal drift is useful.
DRIFT_SENSORS = {
    "ph",
    "bath_temperature",
    "chemical_concentration",
    "humidity",
    "oven_temperature",
    "airflow",
    "paint_pressure",
    "paint_flow",
    "pvc_pressure",
    "water_pressure",
    "conveyor_speed",
    "adhesive_temperature",
}

# Dataclasses

@dataclass
class SensorState:
    """
    Runtime state of a single sensor.

    previous_value:
        Last generated value. Used for temporal continuity.

    drift:
        Slow-moving process drift. This is intentionally small and is
        not the same thing as equipment-health degradation.

    """

    previous_value: Optional[float] = None
    drift: float = 0.0


@dataclass
class StationSensorState:
    """
    Runtime sensor state for one station.
    """

    sensors: Dict[str, SensorState] = field(default_factory=dict)

# Utility functions

def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(value, upper))


def safe_percent_noise(target: float, variation_pct: float) -> float:
    """
    Converts the configuration's percentage variation into a standard
    deviation.

    Example:
        target = 100
        variation_pct = 2
        -> standard deviation = 2

    This is intentionally moderate. The simulator will later add
    equipment/process effects separately.
    """
    return abs(target) * variation_pct / 100.0


def gaussian_around(
    target: float,
    variation_pct: float,
    rng: random.Random,
) -> float:
    sigma = safe_percent_noise(target, variation_pct)

    # Zero-valued targets need a separately chosen noise scale.
    if sigma == 0:
        sigma = 0.001

    return rng.gauss(target, sigma)


def bounded_sensor_value(
    target: float,
    variation_pct: float,
    rng: random.Random,
    minimum: Optional[float] = None,
    maximum: Optional[float] = None,
) -> float:
    value = gaussian_around(target, variation_pct, rng)

    if minimum is not None:
        value = max(minimum, value)

    if maximum is not None:
        value = min(maximum, value)

    return value


def round_sensor_value(value: float, unit: str) -> float:
    """
    Presentation-level rounding only.

    The simulator keeps calculations as floats. This rounding makes
    generated records easier to inspect.
    """
    if unit in {"count"}:
        return float(round(value))
    if unit in {"C", "A", "V", "N", "Nm", "bar", "L/min", "m/s", "%"}:
        return round(value, 2)
    if unit in {"min", "s", "mm", "mm/s", "degree", "DeltaE", "um"}:
        return round(value, 3)
    return round(value, 3)

# Sensor Engine

class SensorEngine:
    """
    Phase 2 process sensor generator.

    The engine reads station definitions from Phase 1 and generates
    one process-sensor record per simulated production event.

    Example
    -------
    engine = SensorEngine("phase1_station_config.json", seed=42)

    reading = engine.generate_station_reading(
        "S29",
        equipment_health=0.90
    )

    print(reading)
    """

    def __init__(
        self,
        config_path: str | Path = DEFAULT_CONFIG_PATH,
        seed: Optional[int] = None,
    ):
        self.config_path = Path(config_path)

        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Phase 1 configuration not found: {self.config_path}"
            )

        with self.config_path.open("r", encoding="utf-8") as f:
            self.config = json.load(f)

        self.stations = {
            station["id"]: station
            for station in self.config["stations"]
        }

        # Phase 1 may represent a parameter either as a full sensor
        # specification dictionary or directly as a numeric target.
        # Normalize both forms here so the rest of Phase 2 can use one
        # consistent representation.
        self._normalize_parameter_specs()

        self.common_parameters = self.config["common_parameters"]

        self.rng = random.Random(seed)

        # Runtime state, separate from Phase 1 configuration.
        self.runtime: Dict[str, StationSensorState] = {}

        for station_id in self.stations:
            self.runtime[station_id] = StationSensorState()

    def _normalize_parameter_specs(self) -> None:
        """
        Normalize Phase 1 parameter definitions.

        Supported input forms:

            "weld_current": {
                "target": 250.0,
                "variation_pct": 2.0,
                "unit": "A"
            }

        or:

            "weld_current": 250.0

        The second form is interpreted as a target with conservative
        default variation. Existing dictionary specifications are
        preserved and only missing fields receive defaults.

        This keeps Phase 2 compatible with the Phase 1 configuration
        without changing the intended target values.
        """

        for station in self.stations.values():
            parameters = station.get("parameters", {})

            for name, raw_spec in list(parameters.items()):

                if isinstance(raw_spec, dict):
                    # Preserve the existing specification.
                    spec = dict(raw_spec)

                    if "target" not in spec:
                        raise ValueError(
                            f"Station {station['id']} parameter "
                            f"'{name}' is a dictionary but has no "
                            "'target'."
                        )

                    spec.setdefault("variation_pct", 2.0)
                    spec.setdefault("unit", "")

                    parameters[name] = spec

                elif isinstance(raw_spec, (int, float)):
                    # Numeric Phase 1 form: value is the target.
                    parameters[name] = {
                        "target": float(raw_spec),
                        "variation_pct": 2.0,
                        "unit": "",
                    }

                else:
                    raise TypeError(
                        f"Station {station['id']} parameter "
                        f"'{name}' has unsupported specification "
                        f"type: {type(raw_spec).__name__}"
                    )

    # Public API

    def generate_station_reading(
        self,
        station_id: str,
        equipment_health: float = 1.0,
        process_health: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Generate one process-sensor snapshot for a station.

        equipment_health:
            1.0 = healthy, 0.0 = severely degraded.

        process_health:
            1.0 = nominal process condition.

        Health is passed in rather than calculated here because
        equipment degradation belongs to Phase 3.
        """

        if station_id not in self.stations:
            raise KeyError(f"Unknown station: {station_id}")

        station = self.stations[station_id]

        equipment_health = clamp(equipment_health, 0.0, 1.0)
        process_health = clamp(process_health, 0.0, 1.0)

        result = {
            "station_id": station_id,
            "station_name": station["name"],
            "station_family": station["family"],
        }

        # First generate the independent/base process variables.
        raw_values: Dict[str, float] = {}

        for name, spec in station.get("parameters", {}).items():


            if name in DERIVED_SENSORS:
                continue

            if name in DISCRETE_SENSORS:
                value = self._generate_discrete_sensor(
                    name=name,
                    spec=spec,
                    station=station,
                    equipment_health=equipment_health,
                    process_health=process_health,
                )

            elif name in DEPENDENT_SENSORS:
                value = self._generate_dependent_sensor(
                    name=name,
                    spec=spec,
                    station=station,
                    existing_values=raw_values,
                    equipment_health=equipment_health,
                    process_health=process_health,
                )

            elif name in EQUIPMENT_HEALTH_SENSORS:
                value = self._generate_equipment_sensor(
                    name=name,
                    spec=spec,
                    station=station,
                    equipment_health=equipment_health,
                )

            else:
                value = self._generate_stable_or_drifting_sensor(
                    name=name,
                    spec=spec,
                    station_id=station_id,
                    process_health=process_health,
                )

            raw_values[name] = value

        # Derived inspection/process measurements.
        self._add_derived_values(
            station=station,
            values=raw_values,
        )

        # Round values for output.
        for name, value in raw_values.items():
            spec = station.get("parameters", {}).get(name, {})
            result[name] = round_sensor_value(
                value,
                spec.get("unit", ""),
            )

        return result

    # Stable / drifting sensors

    def _generate_stable_or_drifting_sensor(
        self,
        name: str,
        spec: Dict[str, Any],
        station_id: str,
        process_health: float,
    ) -> float:

        target = float(spec["target"])
        variation_pct = float(spec.get("variation_pct", 2))

        state = self.runtime[station_id].sensors.setdefault(
            name,
            SensorState(),
        )

        # Slow drift is intentionally much smaller than normal sensor
        # variation. It makes the time series continuous.
        if name in DRIFT_SENSORS:
            drift_step = self.rng.gauss(0.0, 0.01)
            state.drift += drift_step

            # Prevent uncontrolled drift in Phase 2.
            state.drift = clamp(state.drift, -0.05, 0.05)
        else:
            state.drift *= 0.95

        # Slight process-health influence.
        health_effect = 1.0 + (1.0 - process_health) * 0.02

        drifted_target = target * health_effect

        # Normalize drift around target.
        value = drifted_target * (1.0 + state.drift)

        sigma = safe_percent_noise(target, variation_pct)

        if sigma == 0:
            sigma = max(abs(target) * 0.001, 0.001)

        value += self.rng.gauss(0.0, sigma)

        # Keep common physical quantities non-negative.
        if name not in {"ph"}:
            value = max(0.0, value)

        state.previous_value = value

        return value

    # Equipment-health-driven sensors

    def _generate_equipment_sensor(
        self,
        name: str,
        spec: Dict[str, Any],
        station: Dict[str, Any],
        equipment_health: float,
    ) -> float:

        target = float(spec["target"])
        variation_pct = float(spec.get("variation_pct", 8))

        # As equipment health falls:
        # 1. mean vibration increases
        # 2. vibration variability increases
        degradation = 1.0 - equipment_health

        mean_multiplier = 1.0 + 1.5 * degradation
        sigma_multiplier = 1.0 + 2.0 * degradation

        mean = target * mean_multiplier
        sigma = safe_percent_noise(target, variation_pct) * sigma_multiplier

        value = self.rng.gauss(mean, max(sigma, 0.001))
        return max(0.0, value)

    # Dependent sensors

    def _generate_dependent_sensor(
        self,
        name: str,
        spec: Dict[str, Any],
        station: Dict[str, Any],
        existing_values: Dict[str, float],
        equipment_health: float,
        process_health: float,
    ) -> float:

        target = float(spec["target"])
        variation_pct = float(spec.get("variation_pct", 3))

        # ---------------- Paint flow ----------------

        if name == "paint_flow":
            pressure = existing_values.get("paint_pressure")

            if pressure is None:
                pressure = target

            pressure_target = self._target(
                station, "paint_pressure", pressure
            )

            deviation = pressure - pressure_target

            value = target + 0.35 * deviation
            value += self.rng.gauss(
                0,
                max(safe_percent_noise(target, variation_pct), 0.001)
            )

            return max(0.0, value)

        # ---------------- Generic flow rate ----------------

        if name == "flow_rate":
            pressure = (
                existing_values.get("pvc_pressure")
                or existing_values.get("fill_pressure")
                or existing_values.get("pressure")
                or existing_values.get("water_pressure")
            )

            if pressure is not None:
                pressure_target = self._target_from_available_pressure(
                    station,
                    existing_values,
                )
                deviation = pressure - pressure_target

                value = target + 0.30 * deviation
            else:
                value = target

            # Temperature can affect some fluid processes.
            temperature = (
                existing_values.get("temperature")
                or existing_values.get("bath_temperature")
            )

            if temperature is not None:
                temp_target = self._target_from_available_temperature(
                    station,
                    existing_values,
                )
                value += 0.03 * (temperature - temp_target)

            value += self.rng.gauss(
                0,
                max(safe_percent_noise(target, variation_pct), 0.001)
            )

            return max(0.0, value)

        # ---------------- PVC seal thickness ----------------

        if name == "seal_thickness":
            flow = existing_values.get("flow_rate", target)

            flow_target = self._target(
                station, "flow_rate", flow
            )

            value = target + 0.04 * (flow - flow_target)

            pressure = existing_values.get("pvc_pressure")
            if pressure is not None:
                pressure_target = self._target(
                    station, "pvc_pressure", pressure
                )
                value += 0.03 * (pressure - pressure_target)

            value += self.rng.gauss(
                0,
                max(safe_percent_noise(target, variation_pct), 0.001)
            )

            return max(0.0, value)

        # ---------------- Oven cure time ----------------

        if name == "cure_time":
            temperature = existing_values.get("oven_temperature")

            if temperature is None:
                return bounded_sensor_value(
                    target, variation_pct, self.rng, minimum=0
                )

            temperature_target = self._target(
                station, "oven_temperature", temperature
            )

            # Lower oven temperature -> longer cure time.
            temperature_deviation = temperature - temperature_target

            value = target - 0.08 * temperature_deviation

            value += self.rng.gauss(
                0,
                max(safe_percent_noise(target, variation_pct), 0.001)
            )

            return max(0.0, value)

        # ---------------- Fluid filling ----------------

        if name == "fluid_level":
            flow = existing_values.get("flow_rate", target)

            # In a production-event snapshot, level is represented as
            # a near-target filling result. The line engine will later
            # handle the actual fill progression.
            value = target + 0.10 * (
                flow - self._target(station, "flow_rate", flow)
            )

            value += self.rng.gauss(
                0,
                max(safe_percent_noise(target, variation_pct), 0.001)
            )

            return clamp(value, 0.0, 100.0)

        if name == "fill_time":
            flow = existing_values.get("flow_rate")

            if flow is None or flow <= 0:
                flow = self._target(station, "flow_rate", target)

            flow_target = self._target(
                station, "flow_rate", flow
            )

            # Higher flow -> lower fill time.
            value = target * (flow_target / max(flow, 0.001))

            value += self.rng.gauss(
                0,
                max(safe_percent_noise(target, variation_pct), 0.001)
            )

            return max(0.0, value)

        # ---------------- Adhesive flow ----------------

        if name == "adhesive_flow":
            pressure = existing_values.get("pressure", target)
            pressure_target = self._target(
                station, "pressure", pressure
            )

            temperature = existing_values.get(
                "adhesive_temperature",
                self._target(
                    station,
                    "adhesive_temperature",
                    25
                ),
            )

            temperature_target = self._target(
                station,
                "adhesive_temperature",
                temperature,
            )

            # Higher pressure -> more flow.
            # Temperature has a smaller influence.
            value = target
            value += 0.20 * (pressure - pressure_target)
            value += 0.03 * (temperature - temperature_target)

            value += self.rng.gauss(
                0,
                max(safe_percent_noise(target, variation_pct), 0.001)
            )

            return max(0.0, value)

        # ---------------- Torque angle ----------------

        if name == "torque_angle":
            torque = existing_values.get("torque")

            if torque is None:
                torque = self._target(station, "torque", target)

            torque_target = self._target(
                station, "torque", torque
            )

            value = target + 0.05 * (torque - torque_target)

            # Equipment degradation increases variation.
            degradation = 1.0 - equipment_health
            sigma = safe_percent_noise(target, variation_pct)
            sigma *= 1.0 + degradation

            value += self.rng.gauss(0, max(sigma, 0.001))

            return value

        # ---------------- Gap ----------------

        if name == "gap":
            alignment = existing_values.get("alignment")

            if alignment is None:
                alignment = self._target(
                    station, "alignment", target
                )

            alignment_target = self._target(
                station, "alignment", alignment
            )

            value = target + 0.30 * (
                alignment - alignment_target
            )

            value += self.rng.gauss(
                0,
                max(safe_percent_noise(target, variation_pct), 0.001)
            )

            return max(0.0, value)

        # ---------------- Generic temperature ----------------

        if name == "temperature":
            pressure = (
                existing_values.get("pvc_pressure")
                or existing_values.get("pressure")
            )

            value = target

            if pressure is not None:
                pressure_target = self._target_from_available_pressure(
                    station,
                    existing_values,
                )
                value += 0.10 * (pressure - pressure_target)

            value += self.rng.gauss(
                0,
                max(safe_percent_noise(target, variation_pct), 0.001)
            )

            return max(0.0, value)

        # Fallback
        return bounded_sensor_value(
            target,
            variation_pct,
            self.rng,
            minimum=0,
        )

    # Discrete sensors

    def _generate_discrete_sensor(
        self,
        name: str,
        spec: Dict[str, Any],
        station: Dict[str, Any],
        equipment_health: float,
        process_health: float,
    ) -> float:

        target = float(spec["target"])

        if name == "obd_error_count":
            # Phase 2 deliberately avoids random abnormal events.
            # Errors therefore remain zero until a later model
            # explicitly introduces a causal failure condition.
            return 0.0

        if name == "defect_count":
            # Same principle: no random abnormal events in V1.
            # Later inspection logic can derive this from upstream
            # process quality.
            return max(0.0, round(target))

        if name == "burr_count":
            # Stable small count with mild process variation.
            lam = max(target, 0.05)
            # Simple Poisson sampler implemented without NumPy.
            return float(self._poisson(lam))

        return max(0.0, round(target))

    def _poisson(self, lam: float) -> int:
        """
        Small Poisson sampler for discrete count parameters.
        """
        if lam <= 0:
            return 0

        limit = math.exp(-lam)
        product = 1.0
        k = 0

        while product > limit:
            k += 1
            product *= self.rng.random()

        return k - 1

    # Derived values

    def _add_derived_values(
        self,
        station: Dict[str, Any],
        values: Dict[str, float],
    ) -> None:

        params = station.get("parameters", {})

        # Alignment error:
        # derived from the measured alignment deviation.
        if "alignment_error" in params:
            if "alignment" in values:
                alignment_target = self._target(
                    station,
                    "alignment",
                    values["alignment"],
                )

                values["alignment_error"] = abs(
                    values["alignment"] - alignment_target
                )
            elif "camber" in values and "toe_angle" in values:
                values["alignment_error"] = math.sqrt(
                    values["camber"] ** 2 +
                    values["toe_angle"] ** 2
                )
            else:
                values["alignment_error"] = float(
                    params["alignment_error"]["target"]
                )

        # Measurement error is an instrument-noise measurement.
        # It is generated independently because the actual measured
        # quantity is handled by the inspection process.
        if "measurement_error" in params:
            target = float(params["measurement_error"]["target"])
            variation = float(params["measurement_error"].get(
                "variation_pct", 10
            ))

            values["measurement_error"] = abs(
                self.rng.gauss(
                    target,
                    max(safe_percent_noise(target, variation), 0.0001)
                )
            )

        # Inspection score is derived from quality indicators when
        # available. Phase 2 uses a simple process-quality proxy.
        if "inspection_score" in params:
            base = float(params["inspection_score"]["target"])

            penalties = 0.0

            if "surface_defect_score" in values:
                penalties += max(
                    0.0,
                    values["surface_defect_score"] - 2.0
                ) * 2.0

            if "burr_count" in values:
                penalties += max(
                    0.0,
                    values["burr_count"] - 1
                ) * 2.0

            if "paint_thickness" in values:
                target_thickness = self._target(
                    station,
                    "paint_thickness",
                    values["paint_thickness"],
                )
                penalties += abs(
                    values["paint_thickness"] - target_thickness
                ) * 0.05

            if "color_deviation" in values:
                penalties += max(
                    0.0,
                    values["color_deviation"] - 1.0
                ) * 2.0

            score = base - penalties

            values["inspection_score"] = clamp(
                score,
                0.0,
                100.0,
            )

        # Occupancy is derived from buffer level/capacity.
        if "occupancy" in params and station.get("buffer_capacity"):
            if "buffer_level" in values:
                capacity = station["buffer_capacity"]
                values["occupancy"] = clamp(
                    values["buffer_level"] / capacity * 100.0,
                    0.0,
                    100.0,
                )

    # Helpers

    @staticmethod
    def _target(
        station: Dict[str, Any],
        parameter: str,
        fallback: float,
    ) -> float:
        spec = station.get("parameters", {}).get(parameter)
        if spec is None:
            return float(fallback)
        return float(spec["target"])

    def _target_from_available_pressure(
        self,
        station: Dict[str, Any],
        values: Dict[str, float],
    ) -> float:

        for name in (
            "pvc_pressure",
            "fill_pressure",
            "pressure",
            "water_pressure",
        ):
            if name in values:
                return self._target(station, name, values[name])

        return 1.0

    def _target_from_available_temperature(
        self,
        station: Dict[str, Any],
        values: Dict[str, float],
    ) -> float:

        for name in (
            "temperature",
            "bath_temperature",
            "oven_temperature",
        ):
            if name in values:
                return self._target(station, name, values[name])

        return 25.0


# Simple Phase 2 demonstration

def demo() -> None:
    """
    Generate several consecutive readings from selected stations.

    This is only a Phase 2 test and is not the final simulator.
    """

    engine = SensorEngine(DEFAULT_CONFIG_PATH, seed=42)

    print("\nPHASE 2 SENSOR ENGINE DEMO")
    print("=" * 60)

    for station_id in ("S01", "S14", "S15", "S25", "S26", "S29"):
        print(f"\n{station_id}")

        for cycle in range(1, 6):
            reading = engine.generate_station_reading(
                station_id,
                equipment_health=0.95,
                process_health=1.0,
            )

            print(f"Cycle {cycle}: {reading}")


if __name__ == "__main__":
    demo()
