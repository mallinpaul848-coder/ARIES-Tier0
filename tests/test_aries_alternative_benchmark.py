import unittest
from unittest.mock import patch
import urllib.error
from tools.aries_alternative_benchmark import CASES, normalize, parse_target, percentile, request_one


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

    def test_http_error_status_is_preserved(self):
        error = urllib.error.HTTPError("https://example.invalid/v1/chat/completions", 401, "Unauthorized", {}, None)
        with patch("tools.aries_alternative_benchmark.urllib.request.urlopen", side_effect=error):
            result = request_one("https://example.invalid", "model", "hello", 1.0, "fake")
        self.assertEqual(result["status"], 401)
        self.assertIn("HTTPError", result["error"])

    def test_smoke_cases_have_expected_tokens(self):
        self.assertGreaterEqual(len(CASES), 8)
        self.assertTrue(all(category and prompt and expected for category, prompt, expected in CASES))


if __name__ == "__main__":
    unittest.main()
