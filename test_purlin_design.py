import math
import unittest

from utils.pdf_report import generate_purlin_pdf
from utils.purlin_calc import run_purlin_design
from utils.sections import ISMB


class PurlinDesignTests(unittest.TestCase):
    def setUp(self):
        self.input_data = {
            "span_m": 5.0,
            "spacing_m": 1.5,
            "roof_slope_deg": 10.0,
            "dead_load": 0.55,
            "live_load": 0.75,
            "wind_pressure": 0.70,
            "Cp_ext": -0.8,
            "Cp_int": 0.2,
            "fy": 250.0,
            "gm0": 1.10,
            "section_name": "ISMB 300",
            "section_props": ISMB["ISMB 300"],
        }

    def test_purlin_design_returns_real_design_values(self):
        result = run_purlin_design(self.input_data)

        self.assertEqual(result["section_name"], "ISMB 300")
        self.assertEqual(result["overall_status"], "SAFE")
        self.assertGreater(result["Mz_kNm"], 0.0)
        self.assertGreater(result["Mdz_kNm"], result["Mz_kNm"])
        self.assertLess(result["biaxial_ratio"], 1.0)
        self.assertTrue(result["biaxial_ok"])
        self.assertTrue(result["shear_ok"])
        self.assertTrue(result["defl_ok"])
        self.assertTrue(math.isclose(result["sw_kNm"], 44.2 * 9.81 / 1000.0))

    def test_pdf_report_generation_uses_calculation_output(self):
        result = run_purlin_design(self.input_data)
        pdf_bytes = generate_purlin_pdf(result, project="Unit Test Project")

        self.assertGreater(len(pdf_bytes), 5000)
        self.assertEqual(pdf_bytes[:4], b"%PDF")


if __name__ == "__main__":
    unittest.main()
