from __future__ import annotations

import argparse
import re
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


def normalize_column_name(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()


def normalize_sector_name(value: object) -> str:
    text = str(value).strip()
    if not text:
        return "unknown"
    normalized = re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()

    aliases = {
        "road transport highways": ["road transport highways", "road transport & highways", "road transport and highways", "highway", "national highway", "nh", "roads", "road"],
        "railways": ["railways", "railway", "rail", "metro rail"],
        "power": ["power", "solar", "thermal", "wind", "hydro"],
        "petroleum": ["petroleum", "lpg", "pol", "oil", "gas", "natural gas"],
        "telecommunication": ["telecommunication", "telecom", "mobile connectivity", "mobile services"],
        "water resources": ["water resources", "water", "irrigation", "storm water", "river", "drainage", "dam", "canal"],
        "urban development": ["urban development", "urban", "housing", "airport", "building", "infrastructure", "smart city"],
    }

    for canonical, keywords in aliases.items():
        if normalized in keywords or any(keyword in normalized for keyword in keywords):
            return canonical
    return normalized


def infer_sector_from_project_name(project_name: object, state_name: object = "") -> str:
    text = re.sub(r"\s+", " ", str(project_name or "")).strip().lower()
    if not text:
        return normalize_sector_name(state_name)

    sector_rules = [
        ("railways", ["rail", "metro rail", "railway", "rail line"]),
        ("power", ["power", "solar", "thermal", "wind", "hydro"]),
        ("petroleum", ["petroleum", "lpg", "pol", "oil", "gas", "natural gas"]),
        ("road transport highways", ["highway", "national highway", "nh-", "road transport", "roads and services", "roads", "road", "expressway"]),
        ("telecommunication", ["telecom", "telecommunication", "mobile connectivity", "mobile services", "network"]),
        ("water resources", ["water", "irrigation", "storm water", "river", "drainage", "dam", "canal"]),
        ("urban development", ["urban", "housing", "airport", "building", "terminal", "infrastructure", "smart city"]),
    ]

    for sector_name, keywords in sector_rules:
        if any(keyword in text for keyword in keywords):
            return sector_name

    return normalize_sector_name(state_name)


def match_sector_name(user_sector: str, known_sectors: list[str]) -> str:
    if not known_sectors:
        return normalize_sector_name(user_sector)

    target = normalize_sector_name(user_sector)
    if target in known_sectors:
        return target

    target_tokens = set(target.split())
    best_match = target
    best_score = -1

    for sector in known_sectors:
        sector_norm = normalize_sector_name(sector)
        sector_tokens = set(sector_norm.split())
        overlap = len(target_tokens & sector_tokens)
        score = overlap * 3

        if target in sector_norm or sector_norm in target:
            score += 5

        if score > best_score:
            best_score = score
            best_match = sector_norm

    return best_match if best_score > 0 else target


def extract_numeric_values(value: object) -> list[float]:
    if pd.isna(value):
        return []
    if isinstance(value, str):
        cleaned = value.replace(",", "").replace("₹", "").replace("Rs", "").replace("INR", "").replace("₹ ", "").strip()
        numbers = re.findall(r"[-+]?\d+(?:\.\d+)?", cleaned)
        return [float(num) for num in numbers]
    try:
        return [float(value)]
    except (TypeError, ValueError):
        return []


def clean_currency(value: object) -> float:
    nums = extract_numeric_values(value)
    if not nums:
        return float("nan")
    return float(nums[0])


def clean_percentage(value: object) -> float:
    nums = extract_numeric_values(value)
    if not nums:
        return float("nan")
    return float(nums[0])


def parse_cost_pair(value: object) -> tuple[float, float]:
    nums = extract_numeric_values(value)
    if not nums:
        return float("nan"), float("nan")
    if len(nums) == 1:
        return nums[0], nums[0]
    return nums[0], nums[1]


def infer_column_name(data_or_columns, *aliases: str) -> str | None:
    if isinstance(data_or_columns, pd.DataFrame):
        columns = data_or_columns.columns.tolist()
        data = data_or_columns
    else:
        columns = list(data_or_columns)
        data = None

    best_match = None
    best_score = -1

    for alias in aliases:
        target = normalize_column_name(alias)
        for column in columns:
            normalized_column = normalize_column_name(column)
            score = 0
            if target == normalized_column:
                score += 100
            if target in normalized_column or normalized_column in target:
                score += 50
            if set(target.split()).issubset(set(normalized_column.split())):
                score += 25
            if score > 0 and data is not None:
                score += int(data[column].notna().sum())
            if score > best_score:
                best_score = score
                best_match = column

    return best_match


def create_sample_dataset(output_path: Path) -> pd.DataFrame:
    import numpy as np

    rng = np.random.default_rng(42)
    sectors = [
        "Road Transport & Highways",
        "Railways",
        "Water Resources",
        "Power",
        "Urban Development",
        "Telecommunication",
    ]

    rows = []
    for i in range(120):
        sector = sectors[i % len(sectors)]
        original_cost = round(float(rng.uniform(200, 2500)), 2)
        physical_progress = round(float(rng.uniform(12, 90)), 2)
        cost_multiplier = 1 + rng.uniform(0.05, 0.5)
        revised_cost = round(original_cost * cost_multiplier, 2)
        delay_months = round(float(rng.uniform(0, 36)), 2)
        time_overrun_months = round(
            max(
                0.0,
                delay_months + (100.0 - physical_progress) * 0.12 + (original_cost / 300.0) * 0.15 - 8.0,
            ),
            2,
        )
        rows.append(
            {
                "Sector": sector,
                "Original Cost": original_cost,
                "Revised Cost": revised_cost,
                "Physical Progress (%)": physical_progress,
                "Time Delay (Months)": delay_months,
                "Time Overrun (Months)": time_overrun_months,
            }
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    sample_df = pd.DataFrame(rows)
    sample_df.to_csv(output_path, index=False)
    return sample_df


def prepare_dataset(raw_data: pd.DataFrame) -> pd.DataFrame:
    dataset = raw_data.copy()
    dataset.columns = [str(col).strip() for col in dataset.columns]

    def pick_column(*keywords: str) -> str | None:
        for column in dataset.columns:
            normalized = normalize_column_name(column)
            if any(keyword in normalized for keyword in keywords):
                if "sl no" in normalized or "project count" in normalized or "date" in normalized or "doc" in normalized:
                    continue
                return column
        return None

    sector_col = pick_column("sector") or pick_column("state")
    state_col = pick_column("state")
    project_name_col = pick_column("project name")
    original_col = pick_column("orignal cost", "original cost") or pick_column("cost")
    revised_col = pick_column("revised cost")
    progress_col = pick_column("physical progress") or pick_column("progress")
    delay_col = pick_column("time delay", "delay", "months delay")
    time_overrun_col = pick_column("time overrun")

    if not any([sector_col, state_col]):
        raise ValueError("Missing required categorical column: Sector or State")
    if not original_col:
        raise ValueError("Missing required original cost column for training")
    if not progress_col:
        raise ValueError("Missing required progress column for training")

    def infer_sector_row(row: pd.Series) -> str:
        project_name = row[project_name_col] if project_name_col is not None and project_name_col in row else ""
        raw_sector = row[sector_col] if sector_col is not None and sector_col in row else ""
        raw_state = row[state_col] if state_col is not None and state_col in row else ""
        inferred_sector = infer_sector_from_project_name(project_name, raw_state)
        if inferred_sector != "unknown":
            return normalize_sector_name(inferred_sector)
        if raw_sector:
            return normalize_sector_name(raw_sector)
        return normalize_sector_name(raw_state or "unknown")

    dataset["Sector"] = dataset.apply(infer_sector_row, axis=1)

    dataset["Original_Cost"] = dataset[original_col].apply(clean_currency)
    pair_values = dataset[original_col].apply(parse_cost_pair)
    dataset["Original_Cost"] = pair_values.apply(lambda pair: pair[0])

    if revised_col is not None:
        dataset["Revised_Cost"] = dataset[revised_col].apply(clean_currency)
        revised_pair_values = dataset[revised_col].apply(parse_cost_pair)
        dataset["Revised_Cost"] = revised_pair_values.apply(lambda pair: pair[0] if pair[0] else pair[1])
    else:
        dataset["Revised_Cost"] = pair_values.apply(lambda pair: pair[1])

    dataset["Physical_Progress"] = dataset[progress_col].apply(clean_percentage)

    if delay_col is not None:
        dataset["Time_Delay_Months"] = dataset[delay_col].apply(clean_percentage)
    else:
        dataset["Time_Delay_Months"] = 0.0

    if time_overrun_col is not None:
        dataset["Time_Overrun_Months"] = dataset[time_overrun_col].apply(clean_percentage)
    else:
        dataset["Time_Overrun_Months"] = dataset["Time_Delay_Months"].copy()

    dataset["Time_Delay_Months"] = dataset["Time_Delay_Months"].clip(lower=0.0)
    dataset["Time_Overrun_Months"] = dataset["Time_Overrun_Months"].clip(lower=0.0)

    if (
        time_overrun_col is None
        and dataset["Time_Delay_Months"].nunique() > 1
        and dataset["Time_Overrun_Months"].nunique() <= 1
    ):
        dataset["Time_Overrun_Months"] = (
            dataset["Time_Delay_Months"]
            + (100.0 - dataset["Physical_Progress"]) * 0.12
            + (dataset["Original_Cost"] / 500.0) * 0.6
        ).clip(lower=0.0)

    dataset = dataset.dropna(subset=["Original_Cost", "Revised_Cost", "Sector", "Physical_Progress", "Time_Delay_Months", "Time_Overrun_Months"]).copy()
    dataset = dataset[(dataset["Original_Cost"] > 0) & (dataset["Revised_Cost"] > 0)].copy()

    actual_overrun = (dataset["Revised_Cost"] - dataset["Original_Cost"]).clip(lower=0.0)
    delay_factor = dataset["Time_Delay_Months"] * 0.003
    progress_gap = (100.0 - dataset["Physical_Progress"]) * 0.001
    estimated_overrun = dataset["Original_Cost"] * (0.04 + delay_factor + progress_gap)
    dataset["Overrun_Amount"] = actual_overrun.combine(estimated_overrun, lambda actual, estimated: actual if actual > 0 else float(estimated))
    dataset["Overrun_Amount"] = dataset["Overrun_Amount"].clip(lower=0.0)
    return dataset


def resolve_repo_path(path_value: str | Path) -> Path:
    candidate = Path(path_value)
    if candidate.is_absolute():
        return candidate
    project_root = Path(__file__).resolve().parents[1]
    return (project_root / candidate).resolve()


def train_and_save_model(input_csv: str | Path, output_model: str | Path) -> dict:
    input_path = resolve_repo_path(input_csv)
    if not input_path.exists():
        print(f"Dataset not found at {input_path}. Creating a sample dataset for demonstration.")
        input_path = input_path.parent / "sample_project_data.csv"
        create_sample_dataset(input_path)

    raw_data = pd.read_csv(input_path)
    dataset = prepare_dataset(raw_data)

    if dataset.empty:
        raise ValueError("No usable rows after preprocessing. Check the extracted PDF columns.")

    features = ["Sector", "Original_Cost", "Physical_Progress", "Time_Delay_Months"]
    X = dataset[features]
    target_columns = ["Overrun_Amount", "Time_Overrun_Months"]
    y = dataset[target_columns]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    categorical_features = ["Sector"]
    numeric_features = ["Original_Cost", "Physical_Progress", "Time_Delay_Months"]

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", "passthrough", numeric_features),
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
        ]
    )

    base_regressor = XGBRegressor(
        n_estimators=300,
        learning_rate=0.05,
        max_depth=6,
        subsample=0.9,
        colsample_bytree=0.9,
        min_child_weight=1,
        reg_lambda=2.0,
        reg_alpha=0.1,
        gamma=0.05,
        objective="reg:squarederror",
        random_state=42,
        tree_method="hist",
        n_jobs=4,
    )

    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("regressor", MultiOutputRegressor(base_regressor)),
        ]
    )

    print("Training the ML model for both cost overrun and time overrun...")
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    cost_r2 = r2_score(y_test.iloc[:, 0], y_pred[:, 0])
    time_r2 = r2_score(y_test.iloc[:, 1], y_pred[:, 1])
    cost_mae = mean_absolute_error(y_test.iloc[:, 0], y_pred[:, 0])
    time_mae = mean_absolute_error(y_test.iloc[:, 1], y_pred[:, 1])
    cost_rmse = mean_squared_error(y_test.iloc[:, 0], y_pred[:, 0]) ** 0.5
    time_rmse = mean_squared_error(y_test.iloc[:, 1], y_pred[:, 1]) ** 0.5

    print(f"Model Cost Overrun R^2 Score: {cost_r2:.2f}")
    print(f"Model Time Overrun R^2 Score: {time_r2:.2f}")
    print(f"Model Cost Overrun MAE: {cost_mae:.2f}")
    print(f"Model Time Overrun MAE: {time_mae:.2f}")
    print(f"Model Cost Overrun RMSE: {cost_rmse:.2f}")
    print(f"Model Time Overrun RMSE: {time_rmse:.2f}")

    output_path = resolve_repo_path(output_model)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    sector_aliases = sorted(dataset["Sector"].dropna().astype(str).unique().tolist())
    artifact = {
        "model": model,
        "sector_aliases": sector_aliases,
        "target_names": target_columns,
        "metrics": {
            "cost_overrun": {"r2": float(cost_r2), "mae": float(cost_mae), "rmse": float(cost_rmse)},
            "time_overrun": {"r2": float(time_r2), "mae": float(time_mae), "rmse": float(time_rmse)},
        },
    }
    joblib.dump(artifact, output_path)
    print(f"Model saved successfully to {output_path}")

    return {
        "cost_overrun_r2": cost_r2,
        "time_overrun_r2": time_r2,
        "cost_overrun_mae": cost_mae,
        "time_overrun_mae": time_mae,
        "cost_overrun_rmse": cost_rmse,
        "time_overrun_rmse": time_rmse,
        "model_path": str(output_path),
    }


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Train a cost overrun prediction model from tabular project data.")
    parser.add_argument("--input", default=str(project_root / "data" / "extracted_project_data.csv"), help="Path to the extracted project dataset CSV.")
    parser.add_argument("--output", default=str(project_root / "models" / "sih_cost_prediction_model.pkl"), help="Path to save the trained model.")
    args = parser.parse_args()

    train_and_save_model(args.input, args.output)


if __name__ == "__main__":
    main()
