import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from parameter_sweep import build_model_for_config, generate_test_cases
from train_model import create_sample_dataset, prepare_dataset


class ParameterSweepTests(unittest.TestCase):
    def test_generate_test_cases_has_multiple_scenarios(self):
        cases = generate_test_cases()
        self.assertGreater(len(cases), 10)
        self.assertIn('Sector', cases[0])
        self.assertIn('Original_Cost', cases[0])

    def test_model_predicts_two_outputs(self):
        sample_path = ROOT / 'data' / 'sample_validation_data.csv'
        create_sample_dataset(sample_path)
        dataset = prepare_dataset(pd.read_csv(sample_path))
        model, _ = build_model_for_config(dataset, {"n_estimators": 200, "learning_rate": 0.05, "max_depth": 4, "subsample": 0.9, "colsample_bytree": 0.9, "min_child_weight": 1, "reg_lambda": 1.0})
        row = pd.DataFrame([{"Sector": "Power", "Original_Cost": 1200.0, "Physical_Progress": 45.0, "Time_Delay_Months": 10.0}])
        prediction = model.predict(row)[0]
        self.assertEqual(len(prediction), 2)


if __name__ == '__main__':
    unittest.main()
