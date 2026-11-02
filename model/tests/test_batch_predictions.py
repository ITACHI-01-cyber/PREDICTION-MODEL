import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

try:
    from test_batch import run_batch_predictions
except ImportError:
    from model.src.test_batch import run_batch_predictions


class RecordingModel:
    def __init__(self):
        self.input_sizes = []

    def predict(self, inputs):
        self.input_sizes.append(len(inputs))
        return np.array([[25.0, 3.0]])


class BatchPredictionTests(unittest.TestCase):
    def test_predictions_run_one_case_at_a_time_with_a_pause_between_cases(self):
        model = RecordingModel()
        cases = [
            {
                "Sector": "Power",
                "Original_Cost": 1200.0,
                "Physical_Progress": 45.0,
                "Time_Delay_Months": 10.0,
            },
            {
                "Sector": "Railways",
                "Original_Cost": 800.0,
                "Physical_Progress": 15.0,
                "Time_Delay_Months": 6.0,
            },
        ]

        with (
            patch("test_batch.joblib.load", return_value={"model": model}),
            patch("test_batch.time.sleep") as sleep,
        ):
            results = list(run_batch_predictions("unused.pkl", cases, delay_seconds=2.5))

        self.assertEqual(model.input_sizes, [1, 1])
        sleep.assert_called_once_with(2.5)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["Predicted_Cost_Overrun_Crore"], 25.0)
        self.assertEqual(results[1]["Predicted_Time_Overrun_Months"], 3.0)


if __name__ == "__main__":
    unittest.main()
