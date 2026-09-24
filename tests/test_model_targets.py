import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from train_model import prepare_dataset


class ModelTargetTests(unittest.TestCase):
    def test_prepare_dataset_creates_time_overrun_target(self):
        raw = pd.DataFrame(
            {
                'Sector': ['Power'],
                'Original Cost': ['100'],
                'Revised Cost': ['140'],
                'Physical Progress (%)': ['60'],
                'Time Delay (Months)': ['8'],
            }
        )

        prepared = prepare_dataset(raw)

        self.assertIn('Time_Overrun_Months', prepared.columns)
        self.assertEqual(prepared['Time_Overrun_Months'].iloc[0], 8.0)
        self.assertEqual(prepared['Overrun_Amount'].iloc[0], 40.0)


if __name__ == '__main__':
    unittest.main()
