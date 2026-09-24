import os
import re
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = PROJECT_ROOT / 'models' / 'sih_cost_prediction_model.pkl'


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


print("==================================================")
print("   SIH ML Cost + Time Overrun Prediction Model   ")
print("==================================================")

if not MODEL_PATH.exists():
    print(f"Error: Model not found at {MODEL_PATH}. Please train the model first from the project root.")
    print("Example: cd /workspaces/PREDICTION-MODEL && python src/train_model.py")
    sys.exit(1)

artifact = joblib.load(MODEL_PATH)
model = artifact.get("model", artifact) if isinstance(artifact, dict) else artifact
sector_aliases = artifact.get("sector_aliases", []) if isinstance(artifact, dict) else []

print("Model loaded successfully! Ready for live predictions.\n")
print("Type 'exit' or 'quit' at any prompt to stop.\n")

while True:
    try:
        print("-" * 40)
        sector = input("\033[1;36mEnter Sector (e.g., Road Transport & Highways): \033[0m").strip()
        if sector.lower() in ['exit', 'quit']:
            print("Exiting prediction session. Good luck !")
            break

        orig_cost_str = input("\033[1;36mEnter Original Cost (in Crores, e.g., 1500.50): \033[0m").strip()
        if orig_cost_str.lower() in ['exit', 'quit']:
            break

        progress_str = input("\033[1;36mEnter Physical Progress % (e.g., 45.0): \033[0m").strip()
        if progress_str.lower() in ['exit', 'quit']:
            break

        delay_str = input("\033[1;36mEnter Time Delay (in Months, e.g., 12.5): \033[0m").strip()
        if delay_str.lower() in ['exit', 'quit']:
            break

        original_cost = float(orig_cost_str)
        physical_progress = float(progress_str)
        time_delay_months = float(delay_str)
        matched_sector = match_sector_name(sector, sector_aliases)

        input_data = pd.DataFrame({
            'Sector': [matched_sector],
            'Original_Cost': [original_cost],
            'Physical_Progress': [physical_progress],
            'Time_Delay_Months': [time_delay_months],
        })

        prediction = np.asarray(model.predict(input_data))
        if prediction.ndim == 1:
            final_overrun = max(0.0, float(prediction[0]))
            final_time_overrun = max(0.0, time_delay_months)
        else:
            final_overrun = max(0.0, float(prediction[0, 0]))
            final_time_overrun = max(0.0, float(prediction[0, 1]))

        print("\n\033[1;32m[ML Model Output]:\033[0m")
        print(f"  ➔ Predicted Cost Overrun: ₹{final_overrun:.2f} Crore")
        print(f"  ➔ Predicted Time Overrun: {final_time_overrun:.2f} months\n")

    except ValueError:
        print("\n\033[1;31m[Error]: Please enter valid numeric values for cost and progress.\033[0m\n")
    except KeyboardInterrupt:
        print("\nExiting...")
        break
