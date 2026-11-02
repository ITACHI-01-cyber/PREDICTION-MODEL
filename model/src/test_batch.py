from __future__ import annotations

import argparse
from collections.abc import Iterator
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from predict import match_sector_name

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = PROJECT_ROOT / "models" / "sih_cost_prediction_model.pkl"
FEATURE_COLUMNS = (
    "Sector",
    "Original_Cost",
    "Physical_Progress",
    "Time_Delay_Months",
)


def generate_test_cases() -> list[dict[str, str | float]]:
    return [
        {"Sector": "Road Transport & Highways", "Original_Cost": 50.0, "Physical_Progress": 0.0, "Time_Delay_Months": 0.0},
        {"Sector": "Road Transport & Highways", "Original_Cost": 500.0, "Physical_Progress": 10.0, "Time_Delay_Months": 2.0},
        {"Sector": "Road Transport & Highways", "Original_Cost": 1500.0, "Physical_Progress": 40.0, "Time_Delay_Months": 12.0},
        {"Sector": "Road Transport & Highways", "Original_Cost": 3500.0, "Physical_Progress": 90.0, "Time_Delay_Months": 24.0},
        {"Sector": "Power", "Original_Cost": 200.0, "Physical_Progress": 5.0, "Time_Delay_Months": 1.0},
        {"Sector": "Power", "Original_Cost": 1200.0, "Physical_Progress": 45.0, "Time_Delay_Months": 10.0},
        {"Sector": "Power", "Original_Cost": 5000.0, "Physical_Progress": 30.0, "Time_Delay_Months": 18.0},
        {"Sector": "Railways", "Original_Cost": 800.0, "Physical_Progress": 15.0, "Time_Delay_Months": 6.0},
        {"Sector": "Railways", "Original_Cost": 5000.0, "Physical_Progress": 20.0, "Time_Delay_Months": 30.0},
        {"Sector": "Petroleum", "Original_Cost": 800.0, "Physical_Progress": 60.0, "Time_Delay_Months": 8.0},
        {"Sector": "Petroleum", "Original_Cost": 15000.0, "Physical_Progress": 80.0, "Time_Delay_Months": 36.0},
        {"Sector": "Highways", "Original_Cost": 1500.0, "Physical_Progress": 50.0, "Time_Delay_Months": 9.0},
        {"Sector": "Highways", "Original_Cost": 1200.0, "Physical_Progress": 75.0, "Time_Delay_Months": 6.0},
        {"Sector": "Assam", "Original_Cost": 1712.0, "Physical_Progress": 99.5, "Time_Delay_Months": 12.0},
        {"Sector": "Assam", "Original_Cost": 300.0, "Physical_Progress": 5.0, "Time_Delay_Months": 0.0},
        {"Sector": "Transport", "Original_Cost": 900.0, "Physical_Progress": 25.0, "Time_Delay_Months": 14.0},
        {"Sector": "Urban Development", "Original_Cost": 2000.0, "Physical_Progress": 65.0, "Time_Delay_Months": 20.0},
        {"Sector": "Water Resources", "Original_Cost": 6000.0, "Physical_Progress": 55.0, "Time_Delay_Months": 16.0},
        {"Sector": "Telecommunication", "Original_Cost": 450.0, "Physical_Progress": 70.0, "Time_Delay_Months": 4.0},
        {"Sector": "Unknown Sector", "Original_Cost": 1000.0, "Physical_Progress": 35.0, "Time_Delay_Months": 11.0},
    ]


def load_cases(input_path: str | Path | None = None) -> list[dict[str, str | float]]:
    if input_path is None:
        return generate_test_cases()

    cases_path = Path(input_path)
    if not cases_path.is_absolute():
        cases_path = (Path.cwd() / cases_path).resolve()
    cases_df = pd.read_csv(cases_path)

    missing_columns = [column for column in FEATURE_COLUMNS if column not in cases_df.columns]
    if missing_columns:
        raise ValueError(
            f"Input CSV is missing required columns: {', '.join(missing_columns)}. "
            f"Required columns: {', '.join(FEATURE_COLUMNS)}."
        )
    if cases_df.empty:
        raise ValueError(f"Input CSV contains no prediction cases: {cases_path}")

    records = cases_df[list(FEATURE_COLUMNS)].to_dict(orient="records")
    return [{column: record[column] for column in FEATURE_COLUMNS} for record in records]


def run_batch_predictions(
    model_path: str | Path,
    cases: list[dict[str, str | float]],
    delay_seconds: float = 2.0,
) -> Iterator[dict[str, str | float]]:
    if not cases:
        raise ValueError("At least one prediction case is required.")
    if delay_seconds < 0:
        raise ValueError("Prediction delay cannot be negative.")

    artifact = joblib.load(model_path)
    if isinstance(artifact, dict):
        model = artifact.get("model", artifact.get("pipeline", artifact.get("cost_model")))
        sector_aliases = artifact.get("sector_aliases", [])
    else:
        model = artifact
        sector_aliases = []
    if model is None or not hasattr(model, "predict"):
        raise ValueError(f"No usable prediction model found in {model_path}")

    input_df = pd.DataFrame(cases)
    missing_columns = [column for column in FEATURE_COLUMNS if column not in input_df.columns]
    if missing_columns:
        raise ValueError(f"Prediction cases are missing required columns: {', '.join(missing_columns)}")
    input_df = input_df.loc[:, FEATURE_COLUMNS].copy()

    if input_df["Sector"].isna().any() or input_df["Sector"].astype(str).str.strip().eq("").any():
        raise ValueError("Every prediction case must include a non-empty Sector.")

    numeric_columns = ("Original_Cost", "Physical_Progress", "Time_Delay_Months")
    for column in numeric_columns:
        input_df[column] = pd.to_numeric(input_df[column], errors="raise")
        if not np.isfinite(input_df[column].to_numpy()).all():
            raise ValueError(f"Column {column} must contain only finite numeric values.")

    input_df["Sector"] = input_df["Sector"].map(
        lambda sector: match_sector_name(str(sector), sector_aliases)
    )

    for index, (_, row) in enumerate(input_df.iterrows()):
        if index:
            time.sleep(delay_seconds)
        prediction = np.asarray(model.predict(input_df.iloc[index : index + 1]))
        if prediction.ndim == 1:
            prediction = prediction.reshape(1, -1)
        if prediction.ndim != 2 or prediction.shape[0] != 1 or prediction.shape[1] < 1:
            raise ValueError(
                f"Model prediction output for case {index + 1} must contain at least one value."
            )

        cost_overrun = max(0.0, float(prediction[0, 0]))
        time_overrun = (
            max(0.0, float(prediction[0, 1]))
            if prediction.shape[1] >= 2
            else max(0.0, float(row["Time_Delay_Months"]))
        )
        yield {
            "Sector": str(row["Sector"]),
            "Original_Cost": float(row["Original_Cost"]),
            "Physical_Progress": float(row["Physical_Progress"]),
            "Time_Delay_Months": float(row["Time_Delay_Months"]),
            "Predicted_Cost_Overrun_Crore": cost_overrun,
            "Predicted_Time_Overrun_Months": time_overrun,
        }


def print_result(index: int, total: int, result: dict[str, str | float]) -> None:
    print(
        f"Case {index:02d}/{total:02d} | Sector: {result['Sector']} | "
        f"Original cost: INR {result['Original_Cost']:.2f} Cr | "
        f"Progress: {result['Physical_Progress']:.2f}% | "
        f"Delay: {result['Time_Delay_Months']:.2f} months"
    )
    print(
        f"             Predicted cost overrun: "
        f"INR {result['Predicted_Cost_Overrun_Crore']:.2f} Cr | "
        f"Predicted time overrun: "
        f"{result['Predicted_Time_Overrun_Months']:.2f} months",
        flush=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run cost and time overrun predictions for multiple project parameter sets."
    )
    parser.add_argument(
        "--model",
        default=str(MODEL_PATH),
        help="Path to the trained model artifact.",
    )
    parser.add_argument(
        "--input",
        help=(
            "Optional CSV containing Sector, Original_Cost, Physical_Progress, "
            "and Time_Delay_Months columns. If omitted, the built-in test cases are used."
        ),
    )
    parser.add_argument(
        "--delay-seconds",
        type=float,
        default=2.0,
        help="Seconds to wait between individual predictions (default: 2; use 0 for no wait).",
    )
    args = parser.parse_args()
    if args.delay_seconds < 0:
        parser.error("--delay-seconds cannot be negative.")

    cases = load_cases(args.input)
    print("BATCH MODEL PREDICTION TEST")
    print(f"Running {len(cases)} cases one at a time...")
    print("=" * 112)
    for index, result in enumerate(
        run_batch_predictions(args.model, cases, args.delay_seconds),
        start=1,
    ):
        print_result(index, len(cases), result)
    print("=" * 112)
    print(f"Completed predictions for {len(cases)} cases.")


if __name__ == "__main__":
    main()
