import argparse
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import shap


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_model(model_path: str | Path):
    model_bundle = joblib.load(model_path)

    if isinstance(model_bundle, dict):
        if "cost_model" in model_bundle:
            return model_bundle["cost_model"]
        if "model" in model_bundle:
            return model_bundle["model"]
        if "pipeline" in model_bundle:
            return model_bundle["pipeline"]
        raise ValueError(f"Model bundle at {model_path} does not contain a supported pipeline key.")

    return model_bundle


def main():
    parser = argparse.ArgumentParser(description="Explain a project cost-overrun prediction using SHAP values.")
    parser.add_argument("--model", default=str(PROJECT_ROOT / "models" / "sih_cost_prediction_model.pkl"))
    parser.add_argument("--sector", default="Railways")
    parser.add_argument("--original-cost", type=float, default=35000.0)
    parser.add_argument("--physical-progress", type=float, default=12.0)
    parser.add_argument("--time-delay", type=float, default=36.0)
    args = parser.parse_args()

    pipeline = load_model(args.model)
    if not hasattr(pipeline, "named_steps"):
        raise TypeError(f"The loaded object from {args.model} is not a sklearn Pipeline.")

    preprocessor = pipeline.named_steps["preprocessor"]
    regressor = pipeline.named_steps["regressor"]
    estimator = regressor.estimators_[0] if hasattr(regressor, "estimators_") else regressor

    input_df = pd.DataFrame(
        [{
            "Sector": args.sector,
            "Original_Cost": args.original_cost,
            "Physical_Progress": args.physical_progress,
            "Time_Delay_Months": args.time_delay,
        }]
    )

    transformed_input = preprocessor.transform(input_df)
    if hasattr(transformed_input, "toarray"):
        transformed_input = transformed_input.toarray()

    num_features = ["Original_Cost", "Physical_Progress", "Time_Delay_Months"]
    try:
        cat_encoder = preprocessor.named_transformers_["cat"]
        cat_features = list(cat_encoder.get_feature_names_out(["Sector"]))
    except Exception:
        cat_features = []
    all_feature_names = num_features + cat_features

    explainer = shap.TreeExplainer(estimator)
    shap_values = explainer.shap_values(transformed_input)

    if isinstance(shap_values, list):
        shap_values = shap_values[0]
    shap_values = np.asarray(shap_values)

    if shap_values.ndim == 2 and shap_values.shape[0] == 1:
        shap_values = shap_values[0]

    prediction = pipeline.predict(input_df)
    predicted_cost = float(prediction[0, 0]) if np.asarray(prediction).ndim == 2 else float(prediction[0])

    base_value = explainer.expected_value
    if isinstance(base_value, np.ndarray):
        base_value = float(base_value.reshape(-1)[0])

    print("==================================================")
    print("         SHAP MODEL EXPLAINABILITY REPORT         ")
    print("==================================================")
    print(f"Project Profile ➔ {args.sector} | Budget: ₹{args.original_cost} Cr | Delay: {args.time_delay} mo")
    print(f"Predicted Cost Overrun: ₹{max(0.0, predicted_cost):.2f} Crore")
    print("-" * 50)
    print("Feature Contribution Breakdown (SHAP Impact):")

    feature_impacts = sorted(
        zip(all_feature_names, shap_values, transformed_input[0]),
        key=lambda x: abs(x[1]),
        reverse=True,
    )

    for feature, impact, value in feature_impacts:
        if abs(impact) <= 0.01:
            continue
        direction = "↑ Increases Overrun" if impact > 0 else "↓ Decreases Overrun"
        print(f" • {feature} (Value: {value}): ₹{impact:+.2f} Cr [{direction}]")

    print(f"\nBaseline Model Expectation: ₹{base_value:.2f} Cr")
    print("==================================================")


if __name__ == "__main__":
    main()
