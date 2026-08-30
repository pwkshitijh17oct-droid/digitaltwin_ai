from pathlib import Path
import joblib

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "models_v2" / "S01_bottleneck_model_v2.pkl"

artifact = joblib.load(MODEL_PATH)

print("Loaded object type:")
print(type(artifact))

print("\nObject contents:")

if isinstance(artifact, dict):
    print("Dictionary keys:")
    for key in artifact.keys():
        print(" -", key)
else:
    print("Object attributes:")
    print([x for x in dir(artifact) if not x.startswith("_")][:100])

print("\nModel object:")
print(artifact)