"""
Bottleneck ML inference layer.

Loads station-specific bottleneck models and thresholds,
constructs the model feature vector from simulator telemetry,
and returns a standardized prediction result.

Prototype note:
The five interaction features are defined here because their
original training-time feature-engineering source is unavailable.
"""

from pathlib import Path
import json
import joblib
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

MODEL_DIR = BASE_DIR / "ml-files" / "models_v2"
THRESHOLD_FILE = BASE_DIR / "ml-files" / "bottleneck_thresholds_v2.json"


class BottleneckInference:
    def __init__(self):
        self.models = {}
        self.thresholds = {}

        self._load_thresholds()
        self._load_models()

    def _load_thresholds(self):
        with open(THRESHOLD_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.thresholds = data["thresholds"]

    def _load_models(self):
        for path in MODEL_DIR.glob("*_bottleneck_model_v2.pkl"):
            package = joblib.load(path)

            station = package["station"]

            self.models[station] = package

    @staticmethod
    def _safe_ratio(numerator, denominator):
        if denominator is None or pd.isna(denominator) or denominator == 0:
            return 0.0

        if numerator is None or pd.isna(numerator):
            return 0.0

        return float(numerator) / float(denominator)

    def _add_derived_features(self, telemetry):
        telemetry = dict(telemetry)

        queue_length = telemetry.get("queue_length")
        queue_capacity = telemetry.get("queue_capacity")
        waiting_time = telemetry.get("waiting_time_min")
        cycle_time = telemetry.get("cycle_time_min")
        utilization = telemetry.get("utilization_pct")
        equipment_health = telemetry.get("equipment_health")
        process_drift = telemetry.get("process_drift_score")

        telemetry["queue_utilization_ratio"] = self._safe_ratio(
            queue_length,
            queue_capacity,
        )

        telemetry["waiting_cycle_ratio"] = self._safe_ratio(
            waiting_time,
            cycle_time,
        )

        telemetry["queue_wait_interaction"] = (
            float(queue_length or 0) * float(waiting_time or 0)
        )

        telemetry["queue_utilization_interaction"] = (
            float(queue_length or 0) * float(utilization or 0)
        )

        telemetry["health_drift_interaction"] = (
            float(equipment_health or 0) * float(process_drift or 0)
        )

        return telemetry

    def _build_feature_row(self, telemetry, features):
        telemetry = self._add_derived_features(telemetry)

        row = {}

        for feature in features:
            row[feature] = telemetry.get(feature)

        return pd.DataFrame([row], columns=features)

    def predict(self, telemetry):
        station = telemetry.get("station_id")

        if not station:
            raise ValueError("Telemetry is missing station_id.")

        if station not in self.models:
            return {
                "station": station,
                "model_available": False,
                "prediction_available": False,
                "probability": None,
                "threshold": None,
                "predicted_bottleneck": False,
                "horizon_cycles": None,
            }

        package = self.models[station]
        model = package["model"]
        features = package["features"]

        X = self._build_feature_row(telemetry, features)

        probability = float(model.predict_proba(X)[0, 1])

        threshold = float(self.thresholds.get(station, 0.5))

        predicted = probability >= threshold

        return {
            "station": station,
            "model_available": True,
            "prediction_available": True,
            "probability": probability,
            "threshold": threshold,
            "predicted_bottleneck": bool(predicted),
            "horizon_cycles": package["prediction_definition"][
                "future_horizon_cycles"
            ],
            "feature_count": len(features),
        }
