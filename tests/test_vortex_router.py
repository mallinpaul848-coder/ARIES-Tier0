import asyncio
import importlib.util
from pathlib import Path
import unittest

MODULE_PATH = Path(__file__).resolve().parents[1] / "src" / "routing" / "vortex_router.py"
spec = importlib.util.spec_from_file_location("vortex_router", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class VortexRouterTests(unittest.TestCase):
    def test_empty_and_normal_payloads(self):
        router = module.VortexHarmonicDispatcher()
        self.assertEqual(len(router.tier_3_ingest_gate("")), 1)
        self.assertEqual(len(router.tier_3_ingest_gate("ARIES")), 5)

    def test_elapsed_latency_is_duration(self):
        result = module.dispatcher.tier_9_harmonic_synthesis([1.0, 2.0, 3.0])
        self.assertGreaterEqual(result["elapsed_ns"], 0)
        self.assertEqual(result["values_processed"], 3)
        self.assertNotIn("latency_ns", result)

    def test_async_request_releases_counter(self):
        router = module.VortexHarmonicDispatcher()
        result = asyncio.run(router.process_request_async("test"))
        self.assertEqual(result["status"], "success")
        self.assertEqual(router.active_connections, 0)

    def test_nonfinite_input_rejected(self):
        router = module.VortexHarmonicDispatcher()
        with self.assertRaises(ValueError):
            router.tier_6_transformation_matrix([float("nan")])


if __name__ == "__main__":
    unittest.main()
