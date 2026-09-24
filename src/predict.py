from __future__ import annotations

import argparse
import re
from pathlib import Path

import joblib
import pandas as pd


def normalize_sector_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()


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


def parse_float_like(value: str) -> float:
    cleaned = str(value).strip().rstrip("~")
    return float(cleaned)


def predict_overrun(model_path: str | Path, sector: str, original_cost: float, physical_progress: float) -> float:
    artifact = joblib.load(model_path)
    if isinstance(artifact, dict):
        model = artifact.get("model")
        sector_aliases = artifact.get("sector_aliases", [])
    else:
        model = artifact
        sector_aliases = []

    if model is None:
        raise ValueError(f"No valid model found in {model_path}")

    matched_sector = match_sector_name(sector, sector_aliases)
    project = pd.DataFrame(
        {
            "Sector": [matched_sector],
            "Original_Cost": [float(original_cost)],
            "Physical_Progress": [float(physical_progress)],
        }
    )
    prediction = model.predict(project)[0]
    return max(0.0, float(prediction))


def main() -> None:
    parser = argparse.ArgumentParser(description="Predict cost overrun using the trained model.")
    parser.add_argument("--model", default="models/sih_cost_prediction_model.pkl", help="Path to the trained model pickle file.")
    parser.add_argument("--sector", default="Road Transport & Highways", help="Project sector.")
    parser.add_argument("--original-cost", type=parse_float_like, default=1500.50, help="Original project cost in crores.")
    parser.add_argument("--physical-progress", type=parse_float_like, default=45.0, help="Physical progress percentage.")
    args = parser.parse_args()

    predicted_overrun = predict_overrun(args.model, args.sector, args.original_cost, args.physical_progress)
    print(f"Predicted Cost Overrun: ₹{predicted_overrun:.2f} Crore")


if __name__ == "__main__":
    main()
