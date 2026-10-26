import unittest

from aries_math.universal_orchestrator import UniversalPerformanceOrchestrator


class UniversalOrchestratorTests(unittest.TestCase):
    def test_links_components_in_order(self):
        engine = UniversalPerformanceOrchestrator()
        engine.register("normalize", lambda x: x.strip())
        engine.register("reason", lambda x: x + "!")
        self.assertEqual(engine.run("  ARIES  "), "ARIES!")
        report = engine.report()
        self.assertEqual(report["total_calls"], 1)
        self.assertEqual(report["stages"]["normalize"]["calls"], 1)
        self.assertEqual(report["stages"]["reason"]["calls"], 1)

    def test_optional_component_falls_back_and_records_failure(self):
        engine = UniversalPerformanceOrchestrator()
        engine.register("base", lambda x: x + 1)
        def broken(_):
            raise RuntimeError("expected test failure")
        engine.register("optional_experiment", broken, optional=True)
        engine.register("finish", lambda x: x * 2)
        self.assertEqual(engine.run(2), 6)
        self.assertEqual(engine.report()["stages"]["optional_experiment"]["failures"], 1)

    def test_required_failure_is_visible_and_measured(self):
        engine = UniversalPerformanceOrchestrator()
        def broken(_):
            raise RuntimeError("required stage failed")
        engine.register("required", broken)
        with self.assertRaises(RuntimeError):
            engine.run("input")
        report = engine.report()
        self.assertEqual(report["stages"]["required"]["failures"], 1)
        self.assertEqual(report["total_calls"], 1)

    def test_duplicate_names_rejected(self):
        engine = UniversalPerformanceOrchestrator()
        engine.register("same", lambda x: x)
        with self.assertRaises(ValueError):
            engine.register("same", lambda x: x)


if __name__ == "__main__":
    unittest.main()
