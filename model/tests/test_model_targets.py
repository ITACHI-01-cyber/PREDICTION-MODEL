import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from explain_prediction import explain_prediction, format_explanation
from extract_pdf import normalize_project_table
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

    def test_extract_pdf_normalizes_real_project_rows(self):
        raw = pd.DataFrame(
            [[
                '1',
                'Construction of Rudraprayag tunnel on NH-107\n(MoRTH)\n(617967)\n(-) (-)',
                'Uttarakhand',
                '02/2021\n(01/2023)',
                '07/2025\n(07/2026)',
                '251.88\n(251.88)',
                '108.94',
                '99',
            ]],
            columns=[
                'Sl.No',
                'Project Name\n(Agency)\n(Project Code) (Legacy OCMS Code) (PMGID)',
                'State',
                'Date of Approval\n(Start Date)\nMM/YYYY',
                'Orignal/Target DoC\n(Revised DoC)\nMM/YYYY',
                'Orignal Cost\nRevised Cost\nin Rs. Crore',
                'Cumulative\nExpenditure\nin Rs. Crore',
                'Physical Progress\n(%)',
            ],
        )

        normalized = normalize_project_table(raw)

        self.assertEqual(normalized['Sector'].iloc[0], 'road transport highways')
        self.assertAlmostEqual(normalized['Original_Cost'].iloc[0], 251.88)
        self.assertAlmostEqual(normalized['Revised_Cost'].iloc[0], 251.88)
        self.assertAlmostEqual(normalized['Physical_Progress'].iloc[0], 99.0)

    def test_extract_pdf_uses_sector_keywords_from_project_name(self):
        raw = pd.DataFrame(
            [[
                'Patna',
                'Railways',
                '1',
                'Patna Metro Rail Project (Patna Metro Rail Corporation Ltd. [PMRCL])',
                '02/2021',
                '07/2025\n(07/2026)',
                '251.88\n(251.88)',
                '108.94',
                '99',
            ]],
            columns=[
                'State',
                'Sector',
                'Sl No',
                'Project Name\n(Agency)\n(Project Code) (Legacy OCMS Code) (PMGID)',
                'Date\nof\nApproval\n(MM/YYYY)',
                'Date of\nCommissioning\nOriginal\n(Revised)\n{Anticipated}\n(MM/YYYY)',
                'Cost Original\n(Revised)\n{Anticipated}\nin Rs. Crore',
                'Cumulative\nExpenditure\nin Rs. Crore',
                'Physical\nProgress\n(%)',
            ],
        )

        normalized = normalize_project_table(raw)

        self.assertEqual(normalized['Sector'].iloc[0], 'railways')

    def test_explain_prediction_reports_both_cost_and_time_overrun_drivers(self):
        model_path = ROOT / 'models' / 'sih_cost_prediction_model.pkl'
        if not model_path.exists():
            self.skipTest('trained model not available for explainability test')

        report = explain_prediction(model_path, 'Railways', 10000, 25, 12)

        self.assertIn('targets', report)
        self.assertIn('cost_overrun', report['targets'])
        self.assertIn('time_overrun', report['targets'])
        explanation = format_explanation(report)
        self.assertIn('Cost overrun', explanation)
        self.assertIn('Time overrun', explanation)


if __name__ == '__main__':
    unittest.main()
