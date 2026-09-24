import os
from pathlib import Path

import joblib
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = PROJECT_ROOT / 'models' / 'sih_cost_prediction_model.pkl'

if not MODEL_PATH.exists():
    print(f'Model not found at {MODEL_PATH}. Training a stronger model now...')
    import subprocess
    subprocess.run(['python', str(PROJECT_ROOT / 'src' / 'train_model.py')], check=True)

artifact = joblib.load(MODEL_PATH)
model = artifact.get('model', artifact) if isinstance(artifact, dict) else artifact

cases = [
    {'Sector': 'Road Transport & Highways', 'Original_Cost': 500.0, 'Physical_Progress': 10.0},
    {'Sector': 'Road Transport & Highways', 'Original_Cost': 3500.0, 'Physical_Progress': 90.0},
    {'Sector': 'Power', 'Original_Cost': 1200.0, 'Physical_Progress': 45.0},
    {'Sector': 'Railways', 'Original_Cost': 5000.0, 'Physical_Progress': 20.0},
    {'Sector': 'Petroleum', 'Original_Cost': 800.0, 'Physical_Progress': 60.0},
    {'Sector': 'Highways', 'Original_Cost': 1500.0, 'Physical_Progress': 50.0},
    {'Sector': 'Assam', 'Original_Cost': 1712.0, 'Physical_Progress': 99.5},
    {'Sector': 'Power', 'Original_Cost': 5000.0, 'Physical_Progress': 30.0},
    {'Sector': 'Highways', 'Original_Cost': 1200.0, 'Physical_Progress': 75.0},
]

print('==================================================')
print('       BATCH MODEL PREDICTION TEST REPORT         ')
print('==================================================')

for i, case in enumerate(cases, 1):
    input_df = pd.DataFrame([case])
    pred = model.predict(input_df)[0]
    final_pred = max(0.0, float(pred))
    print(f'Test #{i}')
    print(f"  Inputs  ➔ Sector: {case['Sector']} | Cost: ₹{case['Original_Cost']} Cr | Progress: {case['Physical_Progress']}%")
    print(f'  Output  ➔ Predicted Overrun: ₹{final_pred:.2f} Crore')
    print('-' * 50)
