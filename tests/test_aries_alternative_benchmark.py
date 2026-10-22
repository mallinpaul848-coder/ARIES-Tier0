import unittest
from tools.aries_alternative_benchmark import CASES, normalize, parse_target, percentile


class TestAlternativeBenchmark(unittest.TestCase):
    def test_percentile(self):
        self.assertIsNone(percentile([], 95))
        self.assertEqual(percentile([10, 20, 30, 40], 50), 25)
        self.assertEqual(percentile([10, 20, 30, 40], 95), 38.5)

    def test_normalize(self):
        self.assertEqual(normalize(" ARIES-OK. \n"), "aries-ok.")

    def test_target_parse(self):
        self.assertEqual(parse_target("local=http://127.0.0.1:8000,aries-native"), ("local", "http://127.0.0.1:8000", "aries-native"))
        with self.assertRaises(Exception):
            parse_target("bad target")

    def test_smoke_cases_have_expected_tokens(self):
        self.assertGreaterEqual(len(CASES), 8)
        self.assertTrue(all(category and prompt and expected for category, prompt, expected in CASES))


if __name__ == "__main__":
    unittest.main()
