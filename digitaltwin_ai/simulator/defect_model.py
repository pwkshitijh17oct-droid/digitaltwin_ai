"""
DigitalTwin.ai - Defect Generation Engine

Semantics:
- defect_present: vehicle currently carries a defect.
- defect_introduced_here: this station created the defect.
- defect_detected: this station's inspection detected an existing defect.
- defect_present can remain TRUE after detection because detection does not
  magically repair the physical defect.
- S10 and S20 are pure storage buffers and NEVER generate/carry defects.
"""

from __future__ import annotations

import json
import math
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional


BUFFER_STATIONS = {"S10", "S20"}


@dataclass
class DefectResult:
    defect_present: bool = False
    defect_introduced_here: bool = False
    defect_detected: bool = False

    defect_cause: str = "NONE"
    defect_type: str = "NONE"

    defect_severity: float = 0.0
    defect_risk_score: float = 0.0
    defect_probability: float = 0.0

    defect_source_station: str = ""

    process_drift_score: float = 0.0
    input_variation_score: float = 0.0
    fixture_alignment_score: float = 0.0
    environmental_deviation_score: float = 0.0


class DefectEngine:

    PROCESS_GROUPS = {
        "welding": [
            "weld_current",
            "weld_time",
            "temperature",
            "torque",
            "torque_angle",
        ],
        "paint": [
            "paint_pressure",
            "paint_flow",
            "temperature",
            "humidity",
        ],
        "painting": [
            "paint_pressure",
            "paint_flow",
            "temperature",
            "humidity",
        ],
        "oven": [
            "oven_temperature",
            "temperature",
            "airflow",
            "humidity",
            "cure_time",
        ],
        "chemical_process": [
            "ph",
            "bath_temperature",
            "chemical_concentration",
            "flow_rate",
            "pressure",
        ],
        "electrical_assembly": [
            "current",
            "voltage",
            "connector_force",
        ],
        "mechanical_assembly": [
            "torque",
            "torque_angle",
            "alignment",
            "gap",
            "installation_force",
        ],
        "fluid_filling": [
            "flow_rate",
            "fill_time",
            "fluid_level",
            "pressure",
        ],
        "glazing": [
            "adhesive_flow",
            "adhesive_temperature",
            "alignment",
            "gap",
        ],
        "dynamic_testing": [
            "brake_force",
            "wheel_speed",
            "test_time",
        ],
        "leak_testing": [
            "pressure",
            "water_pressure",
            "test_time",
        ],
        "inspection": [
            "measurement_error",
            "alignment_error",
            "inspection_score",
            "surface_defect_score",
        ],
    }

    ENVIRONMENTAL = {
        "humidity",
        "temperature",
        "oven_temperature",
        "airflow",
        "paint_pressure",
        "chemical_concentration",
        "bath_temperature",
        "adhesive_temperature",
        "pressure",
        "water_pressure",
    }

    ALIGNMENT = {
        "alignment",
        "gap",
        "alignment_error",
        "torque_angle",
        "installation_force",
        "connector_force",
    }

    def __init__(
        self,
        config_path: str | Path,
        seed: Optional[int] = 42,
    ):

        self.config_path = Path(
            config_path
        )

        self.config = json.loads(
            self.config_path.read_text(
                encoding="utf-8"
            )
        )

        self.stations = {
            s["id"]: s
            for s in self.config["stations"]
        }

        defect_cfg = (
            self.config
            .get("simulation_config", {})
            .get("defect_model", {})
        )

        self.base_rate = float(
            defect_cfg.get(
                "base_rate_per_process",
                0.00025,
            )
        )

        self.max_probability = float(
            defect_cfg.get(
                "max_probability",
                0.08,
            )
        )

        self.fixture_drift_rate = float(
            defect_cfg.get(
                "fixture_drift_rate",
                0.025,
            )
        )

        self.inspection_detection_probability = float(
            defect_cfg.get(
                "inspection_detection_probability",
                0.90,
            )
        )

        self.minimum_defect_severity = float(
            defect_cfg.get(
                "minimum_defect_severity",
                0.05,
            )
        )

        self.rng = random.Random(
            seed
        )

        self.vehicle_states: Dict[
            int,
            Dict[str, Any],
        ] = {}

        self.station_fixture_state = {
            sid: 0.0
            for sid in self.stations
        }

    # ------------------------------------------------------------------
    # Basic helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _clamp(
        value: float,
        low: float = 0.0,
        high: float = 1.0,
    ) -> float:

        return max(
            low,
            min(
                high,
                float(value),
            ),
        )

    @staticmethod
    def _safe_float(
        value: Any,
        default: float = 0.0,
    ) -> float:

        try:
            return float(value)
        except (
            TypeError,
            ValueError,
        ):
            return default

    def reset(self) -> None:

        self.vehicle_states.clear()

        self.station_fixture_state = {
            sid: 0.0
            for sid in self.stations
        }

    def _vehicle_state(
        self,
        vehicle_id: int,
    ) -> Dict[str, Any]:

        if vehicle_id not in self.vehicle_states:

            self.vehicle_states[
                vehicle_id
            ] = {
                "input_latent": abs(
                    self.rng.gauss(
                        0.0,
                        0.38,
                    )
                ),
                "detected_once": False,
                "defect_present": False,
                "defect_cause": "NONE",
                "defect_type": "NONE",
                "defect_severity": 0.0,
                "source_station": "",
            }

        return self.vehicle_states[
            vehicle_id
        ]

    def _station_family(
        self,
        station: Dict[str, Any],
    ) -> str:

        return str(
            station.get(
                "family",
                "mechanical_assembly",
            )
        ).lower()

    # ------------------------------------------------------------------
    # Condition scores
    # ------------------------------------------------------------------

    def _process_drift_score(
        self,
        station: Dict[str, Any],
        sensors: Dict[str, Any],
    ) -> float:

        params = station.get(
            "parameters",
            {},
        )

        group = self._station_family(
            station
        )

        names = self.PROCESS_GROUPS.get(
            group,
            [],
        )

        deviations = []

        for name in names:

            if name not in sensors:
                continue

            spec = params.get(
                name
            )

            if not spec:
                continue

            target = self._safe_float(
                spec.get(
                    "target",
                    0.0,
                )
            )

            value = self._safe_float(
                sensors[name],
                target,
            )

            variation = abs(
                self._safe_float(
                    spec.get(
                        "variation_pct",
                        1.0,
                    ),
                    1.0,
                )
            )

            scale = max(
                abs(target)
                * variation
                / 100.0,
                1e-6,
            )

            deviations.append(
                min(
                    1.0,
                    abs(
                        value - target
                    ) / (
                        3.0 * scale
                    ),
                )
            )

        return (
            max(deviations)
            if deviations
            else 0.0
        )

    def _input_variation_score(
        self,
        vehicle_id: int,
        station_id: str,
    ) -> float:

        state = self._vehicle_state(
            vehicle_id
        )

        latent = float(
            state.get(
                "input_latent",
                0.0,
            )
        )

        # Small station-dependent deterministic modulation.
        station_factor = (
            (
                sum(
                    ord(c)
                    for c in station_id
                )
                % 17
            )
            / 100.0
        )

        return self._clamp(
            0.70 * latent
            + station_factor
        )

    def _fixture_alignment_score(
        self,
        station: Dict[str, Any],
        sensors: Dict[str, Any],
    ) -> float:

        station_id = station[
            "id"
        ]

        drift = self.station_fixture_state[
            station_id
        ]

        drift += (
            self.rng.random()
            * self.fixture_drift_rate
        )

        drift = self._clamp(
            drift
        )

        self.station_fixture_state[
            station_id
        ] = drift

        values = []

        for name in self.ALIGNMENT:

            if name in sensors:

                value = abs(
                    self._safe_float(
                        sensors[name]
                    )
                )

                values.append(
                    min(
                        1.0,
                        value
                        / max(
                            value * 1.5,
                            1.0,
                        )
                        * 0.35,
                    )
                )

        sensor_component = (
            max(values)
            if values
            else 0.0
        )

        return self._clamp(
            0.65 * drift
            + 0.35 * sensor_component
        )

    def _environmental_score(
        self,
        station: Dict[str, Any],
        sensors: Dict[str, Any],
    ) -> float:

        params = station.get(
            "parameters",
            {},
        )

        deviations = []

        for name in self.ENVIRONMENTAL:

            if name not in sensors:
                continue

            spec = params.get(
                name
            )

            if not spec:
                continue

            target = self._safe_float(
                spec.get(
                    "target",
                    sensors[name],
                )
            )

            value = self._safe_float(
                sensors[name],
                target,
            )

            variation = max(
                self._safe_float(
                    spec.get(
                        "variation_pct",
                        5.0,
                    ),
                    5.0,
                ),
                0.1,
            )

            scale = max(
                abs(target)
                * variation
                / 100.0,
                1e-6,
            )

            deviations.append(
                min(
                    1.0,
                    abs(
                        value - target
                    ) / (
                        3.0 * scale
                    ),
                )
            )

        return (
            max(deviations)
            if deviations
            else 0.0
        )

    def _risk_score(
        self,
        scores: Dict[str, float],
    ) -> float:

        return self._clamp(
            0.28 * scores["process"]
            + 0.24 * scores["input"]
            + 0.24 * scores["fixture"]
            + 0.24 * scores["environment"]
        )

    def _defect_probability(
        self,
        risk_score: float,
    ) -> float:

        return self._clamp(
            self.base_rate
            + 0.018
            * (
                risk_score ** 4
            ),
            0.0,
            self.max_probability,
        )

    # ------------------------------------------------------------------
    # Cause / type / severity
    # ------------------------------------------------------------------

    def _cause_for(
        self,
        scores: Dict[str, float],
    ) -> str:

        names = {
            "process": "PROCESS_DRIFT",
            "input": "INPUT_VARIATION",
            "fixture": "FIXTURE_ALIGNMENT",
            "environment": "ENVIRONMENTAL_DEVIATION",
        }

        return names[
            max(
                scores,
                key=scores.get,
            )
        ]

    def _defect_type(
        self,
        station: Dict[str, Any],
        cause: str,
    ) -> str:

        family = self._station_family(
            station
        )

        mapping = {
            "welding": {
                "PROCESS_DRIFT": "WELD_QUALITY_DEVIATION",
                "INPUT_VARIATION": "WELD_JOINT_VARIATION",
                "FIXTURE_ALIGNMENT": "WELD_ALIGNMENT_DEFECT",
                "ENVIRONMENTAL_DEVIATION": "WELD_CONDITION_DEFECT",
            },
            "paint": {
                "PROCESS_DRIFT": "PAINT_APPLICATION_DEFECT",
                "INPUT_VARIATION": "PAINT_SURFACE_VARIATION",
                "FIXTURE_ALIGNMENT": "PAINT_ALIGNMENT_DEFECT",
                "ENVIRONMENTAL_DEVIATION": "PAINT_ENVIRONMENT_DEFECT",
            },
            "painting": {
                "PROCESS_DRIFT": "PAINT_APPLICATION_DEFECT",
                "INPUT_VARIATION": "PAINT_SURFACE_VARIATION",
                "FIXTURE_ALIGNMENT": "PAINT_ALIGNMENT_DEFECT",
                "ENVIRONMENTAL_DEVIATION": "PAINT_ENVIRONMENT_DEFECT",
            },
            "oven": {
                "PROCESS_DRIFT": "CURE_PROCESS_DEFECT",
                "INPUT_VARIATION": "CURE_INPUT_VARIATION",
                "FIXTURE_ALIGNMENT": "CURE_ALIGNMENT_DEFECT",
                "ENVIRONMENTAL_DEVIATION": "CURE_ENVIRONMENT_DEFECT",
            },
            "inspection": {
                "PROCESS_DRIFT": "INSPECTION_PROCESS_DEFECT",
                "INPUT_VARIATION": "INSPECTION_INPUT_DEFECT",
                "FIXTURE_ALIGNMENT": "INSPECTION_ALIGNMENT_DEFECT",
                "ENVIRONMENTAL_DEVIATION": "INSPECTION_ENVIRONMENT_DEFECT",
            },
        }

        return (
            mapping
            .get(
                family,
                {},
            )
            .get(
                cause,
                "PROCESS_QUALITY_DEVIATION",
            )
        )

    def _severity_from_scores(
        self,
        scores: Dict[str, float],
        risk_score: float,
    ) -> float:

        dominant = max(
            scores.values()
        )

        raw = (
            0.55 * dominant
            + 0.30 * risk_score
            + 0.15
            * self.rng.uniform(
                0.60,
                1.00,
            )
        )

        return self._clamp(
            max(
                self.minimum_defect_severity,
                raw,
            )
        )

    # ------------------------------------------------------------------
    # Public evaluation
    # ------------------------------------------------------------------

    def evaluate(
        self,
        vehicle_id: int,
        station_id: str,
        sensors: Dict[str, Any],
        equipment_health: float = 1.0,
    ) -> Dict[str, Any]:

        del equipment_health

        if station_id not in self.stations:
            raise KeyError(
                f"Unknown station: {station_id}"
            )

        # --------------------------------------------------------------
        # S10 / S20 are pure buffers.
        # --------------------------------------------------------------

        if station_id in BUFFER_STATIONS:

            return asdict(
                DefectResult()
            )

        station = self.stations[
            station_id
        ]

        state = self._vehicle_state(
            vehicle_id
        )

        inherited = bool(
            state[
                "defect_present"
            ]
        )

        scores = {
            "process": self._process_drift_score(
                station,
                sensors,
            ),
            "input": self._input_variation_score(
                vehicle_id,
                station_id,
            ),
            "fixture": self._fixture_alignment_score(
                station,
                sensors,
            ),
            "environment": self._environmental_score(
                station,
                sensors,
            ),
        }

        risk_score = self._risk_score(
            scores
        )

        probability = self._defect_probability(
            risk_score
        )

        introduced = False
        detected = False

        is_inspection = (
            self._station_family(
                station
            )
            == "inspection"
        )

        # --------------------------------------------------------------
        # New defect can only be introduced at a processing station.
        # --------------------------------------------------------------

        if (
            not inherited
            and not is_inspection
            and self.rng.random()
            < probability
        ):

            introduced = True

            cause = self._cause_for(
                scores
            )

            defect_type = self._defect_type(
                station,
                cause,
            )

            severity = (
                self._severity_from_scores(
                    scores,
                    risk_score,
                )
            )

            state.update({
                "defect_present": True,
                "defect_cause": cause,
                "defect_type": defect_type,
                "defect_severity": severity,
                "source_station": station_id,
            })

        # --------------------------------------------------------------
        # Detection only occurs at an inspection station and only for
        # an inherited defect.
        # --------------------------------------------------------------

        if (
            inherited
            and is_inspection
            and not state.get(
                "detected_once",
                False,
            )
        ):

            detected = (
                self.rng.random()
                < self.inspection_detection_probability
            )

            if detected:
                state[
                    "detected_once"
                ] = True

        present = bool(
            state[
                "defect_present"
            ]
        )

        if present:

            cause = state[
                "defect_cause"
            ]

            defect_type = state[
                "defect_type"
            ]

            severity = max(
                self.minimum_defect_severity,
                self._safe_float(
                    state[
                        "defect_severity"
                    ],
                    self.minimum_defect_severity,
                ),
            )

        else:

            cause = "NONE"
            defect_type = "NONE"
            severity = 0.0

        return asdict(
            DefectResult(
                defect_present=present,
                defect_introduced_here=introduced,
                defect_detected=detected,

                defect_cause=(
                    cause
                    if present
                    else "NONE"
                ),

                defect_type=(
                    defect_type
                    if present
                    else "NONE"
                ),

                defect_severity=(
                    self._clamp(
                        severity
                    )
                    if present
                    else 0.0
                ),

                defect_risk_score=risk_score,
                defect_probability=probability,

                defect_source_station=(
                    state[
                        "source_station"
                    ]
                    if present
                    else ""
                ),

                process_drift_score=scores[
                    "process"
                ],
                input_variation_score=scores[
                    "input"
                ],
                fixture_alignment_score=scores[
                    "fixture"
                ],
                environmental_deviation_score=scores[
                    "environment"
                ],
            )
        )

    def vehicle_summary(
        self,
    ) -> Dict[int, Dict[str, Any]]:

        return {
            vehicle_id: dict(state)
            for vehicle_id, state
            in self.vehicle_states.items()
            if state.get(
                "defect_present"
            )
        }


if __name__ == "__main__":

    config = (
        Path(__file__).resolve().parent
        / "phase1_station_config.json"
    )

    if config.exists():

        engine = DefectEngine(
            config,
            seed=42,
        )

        assert not engine.evaluate(
            1,
            "S10",
            {},
        )["defect_present"]

        assert not engine.evaluate(
            1,
            "S20",
            {},
        )["defect_present"]

        result = engine.evaluate(
            1,
            "S01",
            {
                "weld_current": 250,
                "weld_time": 1.0,
            },
        )

        required = {
            "defect_present",
            "defect_introduced_here",
            "defect_detected",
            "defect_cause",
            "defect_type",
            "defect_severity",
            "defect_risk_score",
            "defect_probability",
            "defect_source_station",
            "process_drift_score",
            "input_variation_score",
            "fixture_alignment_score",
            "environmental_deviation_score",
        }

        assert required.issubset(
            result.keys()
        )

        if result["defect_present"]:
            assert result[
                "defect_severity"
            ] > 0.0
        else:
            assert result[
                "defect_severity"
            ] == 0.0

        print(
            "DEFECT MODEL SELF-TEST: PASSED"
        )
