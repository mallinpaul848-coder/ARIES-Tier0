import importlib.util
from pathlib import Path
import unittest

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "aries_power_proof.py"
SPEC = importlib.util.spec_from_file_location("aries_power_proof", MODULE_PATH)
POWER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(POWER)


class EnergyAccountingTests(unittest.TestCase):
    def test_idle_energy_is_subtracted_per_domain(self):
        self.assertEqual(
            POWER.subtract_idle({"package": 12.5, "dram": 3.0},
                                {"package": 4.0, "dram": 1.25}),
            {"package": 8.5, "dram": 1.75},
        )

    def test_missing_idle_domain_is_not_fabricated(self):
        self.assertEqual(
            POWER.subtract_idle({"package": 12.5, "dram": 3.0},
                                {"package": 4.0, "dram": None}),
            {"package": 8.5, "dram": None},
        )

    def test_negative_adjusted_energy_is_preserved_as_noise(self):
        self.assertEqual(
            POWER.subtract_idle({"package": 2.0}, {"package": 3.0}),
            {"package": -1.0},
        )

    def test_numeric_answer_must_be_exact(self):
        self.assertTrue(POWER.exact_numeric_answer("323", "323"))
        self.assertTrue(POWER.exact_numeric_answer("Answer: 323", "323"))
        self.assertFalse(POWER.exact_numeric_answer("The answer is 323, not 324", "323"))
        self.assertFalse(POWER.exact_numeric_answer("I think 323", "323") is False)


if __name__ == "__main__":
    unittest.main()
