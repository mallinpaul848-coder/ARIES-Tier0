"""Regression tests for the ARIES power/market-event microbenchmark."""
import math
import unittest

from aries_math.prise_research_engine import DigitalRootSystem, PRISEProfile, vortex369
from tools.aries_power_trade_bench import (
    aries_feature_decision,
    baseline_decision,
    make_event,
    percentile,
)


class MathDescriptorTests(unittest.TestCase):
    def test_digital_root_boundaries(self):
        self.assertEqual(DigitalRootSystem.compute(0), 0)
        self.assertEqual(DigitalRootSystem.compute(18), 9)
        self.assertEqual(DigitalRootSystem.compute(-18), 9)
        self.assertEqual(DigitalRootSystem.compute(19), 1)

    def test_vortex_cycle(self):
        self.assertEqual([vortex369(n) for n in range(1, 7)], [1, 2, 4, 8, 7, 5])
        self.assertEqual(vortex369(7), 1)
        self.assertEqual(vortex369(0), 0)

    def test_prise_rejects_invalid_weights(self):
        with self.assertRaises(ValueError):
            PRISEProfile(priority=-0.1).score()
        with self.assertRaises(ValueError):
            PRISEProfile(risk=math.inf).score()


class MarketEventBenchmarkTests(unittest.TestCase):
    def test_aries_features_preserve_baseline_action(self):
        for i in range(20_000):
            event = make_event(i)
            self.assertEqual(aries_feature_decision(event)[0], baseline_decision(event))

    def test_event_generation_is_deterministic(self):
        self.assertEqual([make_event(i) for i in range(100)],
                         [make_event(i) for i in range(100)])

    def test_percentile_interpolation(self):
        self.assertEqual(percentile([0, 10], 50), 5.0)
        self.assertEqual(percentile([4], 99), 4.0)
        self.assertIsNone(percentile([], 50))


if __name__ == "__main__":
    unittest.main()
