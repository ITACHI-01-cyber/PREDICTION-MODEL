from __future__ import annotations

import argparse
import re
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBRegressor


def normalize_column_name(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()


def normalize_sector_name(value: object) -> str:
    text = str(value).strip()
    if not text:
        return "unknown"
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


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
        rows.append(
            {
                "Sector": sector,
                "Original Cost": original_cost,
                "Revised Cost": revised_cost,
                "Physical Progress (%)": physical_progress,
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
    original_col = pick_column("orignal cost", "original cost") or pick_column("cost")
    progress_col = pick_column("physical progress") or pick_column("progress")

    if not any([sector_col, pick_column("state")]):
        raise ValueError("Missing required categorical column: Sector or State")
    if not original_col:
        raise ValueError("Missing required original cost column for training")
    if not progress_col:
        raise ValueError("Missing required progress column for training")

    dataset["Sector"] = (dataset[sector_col] if sector_col else dataset[pick_column("state")]).astype(str)
    dataset["Sector"] = dataset["Sector"].apply(normalize_sector_name)

    dataset["Original_Cost"] = dataset[original_col].apply(clean_currency)
    pair_values = dataset[original_col].apply(parse_cost_pair)
    dataset["Original_Cost"] = pair_values.apply(lambda pair: pair[0])
    dataset["Revised_Cost"] = pair_values.apply(lambda pair: pair[1])
    dataset["Physical_Progress"] = dataset[progress_col].apply(clean_percentage)

    dataset = dataset.dropna(subset=["Original_Cost", "Revised_Cost", "Sector", "Physical_Progress"]).copy()
    dataset = dataset[(dataset["Original_Cost"] > 0) & (dataset["Revised_Cost"] > 0)].copy()
    dataset["Overrun_Amount"] = dataset["Revised_Cost"] - dataset["Original_Cost"]
    return dataset


def train_and_save_model(input_csv: str | Path, output_model: str | Path) -> dict:
    input_path = Path(input_csv)
    if not input_path.exists():
        print(f"Dataset not found at {input_path}. Creating a sample dataset for demonstration.")
        input_path = input_path.parent / "sample_project_data.csv"
        create_sample_dataset(input_path)

    raw_data = pd.read_csv(input_path)
    dataset = prepare_dataset(raw_data)

    if dataset.empty:
        raise ValueError("No usable rows after preprocessing. Check the extracted PDF columns.")

    features = ["Sector", "Original_Cost", "Physical_Progress"]
    X = dataset[features]
    y = dataset["Overrun_Amount"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    categorical_features = ["Sector"]
    numeric_features = ["Original_Cost", "Physical_Progress"]

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", "passthrough", numeric_features),
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
        ]
    )

    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "regressor",
                XGBRegressor(
                    n_estimators=800,
                    learning_rate=0.025,
                    max_depth=10,
                    subsample=0.9,
                    colsample_bytree=0.9,
                    min_child_weight=1,
                    reg_lambda=2.0,
                    reg_alpha=0.1,
                    gamma=0.05,
                    objective="reg:squarederror",
                    random_state=42,
                    tree_method="hist",
                ),
            ),
        ]
    )

    print("Training the ML model...")
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = mean_squared_error(y_test, y_pred, squared=False)

    print(f"Model R^2 Score on test data: {r2:.2f}")
    print(f"Model MAE: {mae:.2f}")
    print(f"Model RMSE: {rmse:.2f}")

    output_path = Path(output_model)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    sector_aliases = sorted(dataset["Sector"].dropna().astype(str).unique().tolist())
    artifact = {
        "model": model,
        "sector_aliases": sector_aliases,
        "metrics": {
            "r2": float(r2),
            "mae": float(mae),
            "rmse": float(rmse),
        },
    }
    joblib.dump(artifact, output_path)
    print(f"Model saved successfully to {output_path}")

    return {"r2_score": r2, "mae": mae, "rmse": rmse, "model_path": str(output_path)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Train a cost overrun prediction model from tabular project data.")
    parser.add_argument("--input", default="data/extracted_project_data.csv", help="Path to the extracted project dataset CSV.")
    parser.add_argument("--output", default="models/sih_cost_prediction_model.pkl", help="Path to save the trained model.")
    args = parser.parse_args()

    train_and_save_model(args.input, args.output)


if __name__ == "__main__":
    main()
