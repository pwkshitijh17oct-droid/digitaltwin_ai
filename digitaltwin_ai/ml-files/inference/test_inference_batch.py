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
    inference = BottleneckInference()

    df = pd.read_csv(TELEMETRY_FILE)

    results = []

    for station in sorted(inference.models.keys()):
        station_df = df[df["station_id"] == station].tail(100)

        probabilities = []
        positives = 0

        for _, row in station_df.iterrows():
            result = inference.predict(row.to_dict())

            probability = result["probability"]

            probabilities.append(probability)

            if result["predicted_bottleneck"]:
                positives += 1

        results.append(
            {
                "Station": station,
                "Samples": len(probabilities),
                "Min Probability": min(probabilities),
                "Mean Probability": sum(probabilities) / len(probabilities),
                "Max Probability": max(probabilities),
                "Positive Predictions": positives,
                "Threshold": inference.thresholds[station],
            }
        )

    result_df = pd.DataFrame(results)

    print("\nBATCH INFERENCE TEST")
    print("=" * 100)

    print(
        result_df.to_string(
            index=False,
            formatters={
                "Min Probability": "{:.6f}".format,
                "Mean Probability": "{:.6f}".format,
                "Max Probability": "{:.6f}".format,
                "Threshold": "{:.6f}".format,
            },
        )
    )


if __name__ == "__main__":
    main()