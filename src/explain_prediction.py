from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import shap

from predict import match_sector_name


def load_model_bundle(model_path: str | Path):
    artifact = joblib.load(model_path)
    if isinstance(artifact, dict):
        return artifact.get("model"), artifact.get("sector_aliases", []), artifact.get("target_names", ["Overrun_Amount", "Time_Overrun_Months"])
    return artifact, [], ["Overrun_Amount", "Time_Overrun_Months"]


def _pretty_feature_name(feature_name: str) -> str:
    cleaned = feature_name.replace("num__", "").replace("cat__", "").replace("Sector_", "").replace("__", " ")
    cleaned = cleaned.replace("Original_Cost", "Original Cost")
    cleaned = cleaned.replace("Physical_Progress", "Physical Progress")
    cleaned = cleaned.replace("Time_Delay_Months", "Time Delay")
    cleaned = cleaned.replace("_", " ")
    return cleaned.strip()


def _build_feature_row(sector: str, original_cost: float, physical_progress: float, time_delay_months: float) -> pd.DataFrame:
    return pd.DataFrame([
        {
            "Sector": sector,
            "Original_Cost": float(original_cost),
            "Physical_Progress": float(physical_progress),
            "Time_Delay_Months": float(time_delay_months),
        }
    ])


def _get_target_explainer(model, target_index: int):
    return shap.TreeExplainer(model.named_steps["regressor"].estimators_[target_index])


def explain_prediction(
    model_path: str | Path,
    sector: str,
    original_cost: float,
    physical_progress: float,
    time_delay_months: float = 0.0,
) -> dict:
    model, sector_aliases, target_names = load_model_bundle(model_path)
    matched_sector = match_sector_name(sector, sector_aliases)
    feature_row = _build_feature_row(matched_sector, original_cost, physical_progress, time_delay_months)

    pipeline = model
    preprocessor = pipeline.named_steps["preprocessor"]
    transformed = preprocessor.transform(feature_row)
    if hasattr(transformed, "toarray"):
        transformed = transformed.toarray()

    feature_names = preprocessor.get_feature_names_out().tolist()
    prediction_values = np.asarray(pipeline.predict(feature_row)).ravel()
    cost_explainer = _get_target_explainer(pipeline, 0)
    time_explainer = _get_target_explainer(pipeline, 1)

    def build_target_report(target_index: int, label: str):
        estimator = pipeline.named_steps["regressor"].estimators_[target_index]
        explainer = shap.TreeExplainer(estimator)
        shap_values = explainer.shap_values(transformed)
        if isinstance(shap_values, list):
            shap_values = shap_values[0]
        shap_values = np.asarray(shap_values).reshape(-1, transformed.shape[1])

        feature_importance = []
        for feature_name, raw_value, contribution in zip(feature_names, transformed[0], shap_values[0]):
            if abs(contribution) < 1e-8:
                continue
            display_name = _pretty_feature_name(feature_name)
            if "Sector" in feature_name:
                display_name = f"Sector = {feature_name.split('Sector_')[-1].replace('_', ' ')}"
            feature_importance.append({
                "feature": display_name,
                "raw_value": float(raw_value),
                "contribution": float(contribution),
            })

        sorted_features = sorted(feature_importance, key=lambda x: abs(x["contribution"]), reverse=True)
        return {
            "label": label,
            "prediction": float(prediction_values[target_index]),
            "base_value": float(np.asarray(explainer.expected_value).ravel()[0]),
            "feature_importance": sorted_features,
        }

    report = {
        "sector": matched_sector,
        "targets": {
            "cost_overrun": build_target_report(0, target_names[0]),
            "time_overrun": build_target_report(1, target_names[1]),
        },
    }
    return report


def format_explanation(report: dict) -> str:
    cost_target = report["targets"]["cost_overrun"]
    time_target = report["targets"]["time_overrun"]

    lines = [
        "SHAP explanation for the current project:",
        f"Matched sector: {report['sector']}",
        "",
        "Cost overrun:",
        f"- Baseline: ₹{cost_target['base_value']:.2f} Crore",
        f"- Predicted: ₹{cost_target['prediction']:.2f} Crore",
        "- Top drivers:",
    ]

    for item in cost_target["feature_importance"][:5]:
        sign = "+" if item["contribution"] >= 0 else "-"
        lines.append(f"  * {item['feature']}: value={item['raw_value']} -> SHAP impact {sign}₹{abs(item['contribution']):.2f} Crore")

    lines.extend([
        "",
        "Time overrun:",
        f"- Baseline: {time_target['base_value']:.2f} months",
        f"- Predicted: {time_target['prediction']:.2f} months",
        "- Top drivers:",
    ])

    for item in time_target["feature_importance"][:5]:
        sign = "+" if item["contribution"] >= 0 else "-"
        lines.append(f"  * {item['feature']}: value={item['raw_value']} -> SHAP impact {sign}{abs(item['contribution']):.2f} months")

    return "\n".join(lines)


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Explain cost and time overrun using SHAP values.")
    parser.add_argument("--model", default=str(project_root / "models" / "sih_cost_prediction_model.pkl"), help="Path to the trained model pickle file.")
    parser.add_argument("--sector", default="Railways", help="Project sector.")
    parser.add_argument("--original-cost", type=float, default=10000.0, help="Original project cost in crores.")
    parser.add_argument("--physical-progress", type=float, default=25.0, help="Physical progress percentage.")
    parser.add_argument("--time-delay", type=float, default=12.0, help="Time delay in months.")
    args = parser.parse_args()

    report = explain_prediction(
        args.model,
        args.sector,
        args.original_cost,
        args.physical_progress,
        args.time_delay,
    )
    print(format_explanation(report))


if __name__ == "__main__":
    main()
