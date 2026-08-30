from pathlib import Path
import pandas as pd

from bottleneck_inference import BottleneckInference


BASE_DIR = Path(__file__).resolve().parents[2]

TELEMETRY_FILE = (
    BASE_DIR
    / "simulator"
    / "live simulation data"
    / "generation7"
    / "telemetry.csv"
)


def main():
    print("Loading bottleneck inference layer...")

    inference = BottleneckInference()

    print(f"Models loaded: {len(inference.models)}")
    print(f"Thresholds loaded: {len(inference.thresholds)}")

    df = pd.read_csv(TELEMETRY_FILE)

    print(f"Telemetry rows: {len(df)}")
    print(f"Telemetry columns: {len(df.columns)}")

    print("\nTesting one row per station...\n")

    tested = 0
    predicted_positive = 0

    for station in sorted(df["station_id"].dropna().unique()):
        station_rows = df[df["station_id"] == station]

        if station not in inference.models:
            print(f"{station}: NO MODEL")
            continue

        row = station_rows.iloc[-1].to_dict()

        result = inference.predict(row)

        print(
            f"{station}: "
            f"probability={result['probability']:.6f}, "
            f"threshold={result['threshold']:.6f}, "
            f"prediction={result['predicted_bottleneck']}, "
            f"features={result['feature_count']}"
        )

        tested += 1

        if result["predicted_bottleneck"]:
            predicted_positive += 1

    print("\n----------------------------------------")
    print("INFERENCE TEST SUMMARY")
    print("----------------------------------------")
    print(f"Stations with models tested : {tested}")
    print(f"Predicted bottleneck        : {predicted_positive}")
    print("----------------------------------------")


if __name__ == "__main__":
    main()