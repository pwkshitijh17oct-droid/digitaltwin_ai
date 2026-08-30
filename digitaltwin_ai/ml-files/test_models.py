from pathlib import Path
import joblib
import json


BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "models_v2"
THRESHOLD_FILE = BASE_DIR / "bottleneck_thresholds_v2.json"


print("Checking ML model files...\n")

model_files = sorted(MODEL_DIR.glob("*_bottleneck_model_v2.pkl"))

print(f"Found {len(model_files)} model files.")

for model_path in model_files:
    try:
        artifact = joblib.load(model_path)

        model = artifact["model"]
        features = artifact.get("features", [])
        target = artifact.get("target")
        station = artifact.get("station")

        print(
            f"✓ {station}: "
            f"{len(features)} features, "
            f"target={target}"
        )

    except Exception as e:
        print(f"✗ {model_path.name}: {e}")


print("\nChecking threshold file...")

try:
    with open(THRESHOLD_FILE, "r", encoding="utf-8") as f:
        thresholds = json.load(f)

    print(f"✓ Loaded thresholds for {len(thresholds)} stations")

except Exception as e:
    print(f"✗ Threshold file error: {e}")