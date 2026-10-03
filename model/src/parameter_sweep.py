from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.multioutput import MultiOutputRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBRegressor

from train_model import prepare_dataset


def resolve_repo_path(path_value: str | Path) -> Path:
    candidate = Path(path_value)
    if candidate.is_absolute():
        return candidate
    return (Path(__file__).resolve().parents[1] / candidate).resolve()


def generate_test_cases() -> list[dict]:
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
        {"Sector": "Urban Development", "Original_Cost": 2000.0, "Physical_Progress": 65.0, "Time_Delay_Months": 20.0},
        {"Sector": "Water Resources", "Original_Cost": 6000.0, "Physical_Progress": 55.0, "Time_Delay_Months": 16.0},
        {"Sector": "Telecommunication", "Original_Cost": 450.0, "Physical_Progress": 70.0, "Time_Delay_Months": 4.0},
        {"Sector": "Unknown Sector", "Original_Cost": 1000.0, "Physical_Progress": 35.0, "Time_Delay_Months": 11.0},
    ]


def build_model_for_config(dataset: pd.DataFrame, config: dict) -> tuple[Pipeline, dict]:
    features = ["Sector", "Original_Cost", "Physical_Progress", "Time_Delay_Months"]
    target_cols = ["Overrun_Amount", "Time_Overrun_Months"]
    X = dataset[features]
    y = dataset[target_cols].astype(float)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", "passthrough", ["Original_Cost", "Physical_Progress", "Time_Delay_Months"]),
            ("cat", OneHotEncoder(handle_unknown="ignore"), ["Sector"]),
        ]
    )

    xgb_model = XGBRegressor(
        objective="reg:squarederror",
        random_state=42,
        tree_method="hist",
        **config,
    )

    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("regressor", MultiOutputRegressor(xgb_model)),
        ]
    )

    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    cost_r2 = r2_score(y_test.iloc[:, 0], y_pred[:, 0])
    time_r2 = r2_score(y_test.iloc[:, 1], y_pred[:, 1])
    cost_mae = mean_absolute_error(y_test.iloc[:, 0], y_pred[:, 0])
    time_mae = mean_absolute_error(y_test.iloc[:, 1], y_pred[:, 1])
    cost_rmse = mean_squared_error(y_test.iloc[:, 0], y_pred[:, 0]) ** 0.5
    time_rmse = mean_squared_error(y_test.iloc[:, 1], y_pred[:, 1]) ** 0.5

    metrics = {
        "cost_r2": float(cost_r2),
        "time_r2": float(time_r2),
        "cost_mae": float(cost_mae),
        "time_mae": float(time_mae),
        "cost_rmse": float(cost_rmse),
        "time_rmse": float(time_rmse),
    }
    return model, metrics


def run_parameter_sweep(input_csv: str | Path, output_summary: str | Path, output_model: str | Path) -> dict:
    input_path = resolve_repo_path(input_csv)
    raw_data = pd.read_csv(input_path)
    dataset = prepare_dataset(raw_data)

    config_grid = [
        {"n_estimators": 300, "learning_rate": 0.03, "max_depth": 4, "subsample": 0.8, "colsample_bytree": 0.8, "min_child_weight": 1, "reg_lambda": 1.0},
        {"n_estimators": 500, "learning_rate": 0.03, "max_depth": 6, "subsample": 0.9, "colsample_bytree": 0.9, "min_child_weight": 2, "reg_lambda": 1.5},
        {"n_estimators": 800, "learning_rate": 0.025, "max_depth": 8, "subsample": 0.9, "colsample_bytree": 0.9, "min_child_weight": 1, "reg_lambda": 2.0},
        {"n_estimators": 1000, "learning_rate": 0.02, "max_depth": 10, "subsample": 1.0, "colsample_bytree": 1.0, "min_child_weight": 1, "reg_lambda": 2.5},
    ]

    results = []
    for config in config_grid:
        model, metrics = build_model_for_config(dataset, config)
        case_predictions = []
        for case in generate_test_cases():
            row = pd.DataFrame([case])
            prediction = model.predict(row)[0]
            case_predictions.append({
                "sector": case["Sector"],
                "original_cost": case["Original_Cost"],
                "physical_progress": case["Physical_Progress"],
                "time_delay_months": case["Time_Delay_Months"],
                "cost_overrun": float(max(0.0, prediction[0])),
                "time_overrun": float(max(0.0, prediction[1])),
            })

        results.append({
            "config": config,
            "metrics": metrics,
            "case_predictions": case_predictions,
        })

    best_result = max(results, key=lambda item: item["metrics"]["time_r2"] + item["metrics"]["cost_r2"])
    best_model = build_model_for_config(dataset, best_result["config"])[0]

    summary_path = resolve_repo_path(output_summary)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps({"best_config": best_result["config"], "best_metrics": best_result["metrics"]}, indent=2))

    model_path = resolve_repo_path(output_model)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    artifact = {
        "model": best_model,
        "sector_aliases": sorted(dataset["Sector"].dropna().unique().tolist()),
        "target_names": ["Overrun_Amount", "Time_Overrun_Months"],
        "best_config": best_result["config"],
        "metrics": best_result["metrics"],
    }
    joblib.dump(artifact, model_path)

    return {
        "best_config": best_result["config"],
        "best_metrics": best_result["metrics"],
        "model_path": str(model_path),
        "summary_path": str(summary_path),
    }


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Run a parameter sweep across the project model and save the best-performing variant.")
    parser.add_argument("--input", default=str(project_root / "data" / "extracted_project_data.csv"), help="CSV file used for training.")
    parser.add_argument("--summary", default=str(project_root / "models" / "sweep_summary.json"), help="Where to save the sweep summary JSON.")
    parser.add_argument("--output", default=str(project_root / "models" / "best_sweep_model.pkl"), help="Where to save the best-performing trained model.")
    args = parser.parse_args()

    outcome = run_parameter_sweep(args.input, args.summary, args.output)
    print(json.dumps(outcome, indent=2))


if __name__ == "__main__":
    main()
