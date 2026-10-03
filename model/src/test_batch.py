import os
from pathlib import Path

import joblib
import numpy as np
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
    {'Sector': 'Road Transport & Highways', 'Original_Cost': 50.0, 'Physical_Progress': 0.0, 'Time_Delay_Months': 0.0},
    {'Sector': 'Road Transport & Highways', 'Original_Cost': 500.0, 'Physical_Progress': 10.0, 'Time_Delay_Months': 2.0},
    {'Sector': 'Road Transport & Highways', 'Original_Cost': 1500.0, 'Physical_Progress': 40.0, 'Time_Delay_Months': 12.0},
    {'Sector': 'Road Transport & Highways', 'Original_Cost': 3500.0, 'Physical_Progress': 90.0, 'Time_Delay_Months': 24.0},
    {'Sector': 'Power', 'Original_Cost': 200.0, 'Physical_Progress': 5.0, 'Time_Delay_Months': 1.0},
    {'Sector': 'Power', 'Original_Cost': 1200.0, 'Physical_Progress': 45.0, 'Time_Delay_Months': 10.0},
    {'Sector': 'Power', 'Original_Cost': 5000.0, 'Physical_Progress': 30.0, 'Time_Delay_Months': 18.0},
    {'Sector': 'Railways', 'Original_Cost': 800.0, 'Physical_Progress': 15.0, 'Time_Delay_Months': 6.0},
    {'Sector': 'Railways', 'Original_Cost': 5000.0, 'Physical_Progress': 20.0, 'Time_Delay_Months': 30.0},
    {'Sector': 'Petroleum', 'Original_Cost': 800.0, 'Physical_Progress': 60.0, 'Time_Delay_Months': 8.0},
    {'Sector': 'Petroleum', 'Original_Cost': 15000.0, 'Physical_Progress': 80.0, 'Time_Delay_Months': 36.0},
    {'Sector': 'Highways', 'Original_Cost': 1500.0, 'Physical_Progress': 50.0, 'Time_Delay_Months': 9.0},
    {'Sector': 'Highways', 'Original_Cost': 1200.0, 'Physical_Progress': 75.0, 'Time_Delay_Months': 6.0},
    {'Sector': 'Assam', 'Original_Cost': 1712.0, 'Physical_Progress': 99.5, 'Time_Delay_Months': 12.0},
    {'Sector': 'Assam', 'Original_Cost': 300.0, 'Physical_Progress': 5.0, 'Time_Delay_Months': 0.0},
    {'Sector': 'Transport', 'Original_Cost': 900.0, 'Physical_Progress': 25.0, 'Time_Delay_Months': 14.0},
    {'Sector': 'Urban Development', 'Original_Cost': 2000.0, 'Physical_Progress': 65.0, 'Time_Delay_Months': 20.0},
    {'Sector': 'Water Resources', 'Original_Cost': 6000.0, 'Physical_Progress': 55.0, 'Time_Delay_Months': 16.0},
    {'Sector': 'Telecommunication', 'Original_Cost': 450.0, 'Physical_Progress': 70.0, 'Time_Delay_Months': 4.0},
    {'Sector': 'Unknown Sector', 'Original_Cost': 1000.0, 'Physical_Progress': 35.0, 'Time_Delay_Months': 11.0},
]

print('==================================================')
print('       BATCH MODEL PREDICTION TEST REPORT         ')
print('==================================================')

for i, case in enumerate(cases, 1):
    input_df = pd.DataFrame([case])
    pred = np.asarray(model.predict(input_df)).reshape(-1)

    if pred.size >= 2:
        final_cost_pred = max(0.0, float(pred[0]))
        final_time_pred = max(0.0, float(pred[1]))
        output_desc = f'  Output  ➔ Predicted Cost Overrun: ₹{final_cost_pred:.2f} Crore | Predicted Time Overrun: {final_time_pred:.2f} months'
    else:
        final_pred = max(0.0, float(pred[0]))
        output_desc = f'  Output  ➔ Predicted Overrun: ₹{final_pred:.2f} Crore'

    print(f'Test #{i}')
    print(
        f"  Inputs  ➔ Sector: {case['Sector']} | Cost: ₹{case['Original_Cost']} Cr | "
        f"Progress: {case['Physical_Progress']}% | Delay: {case['Time_Delay_Months']} months"
    )
    print(output_desc)
    print('-' * 80)
