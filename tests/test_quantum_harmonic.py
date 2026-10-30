import unittest
from aries_math.quantum_harmonic import HarmonicStateVector, digital_root, harmonic_phase

class HarmonicQuantumTests(unittest.TestCase):
    def test_digital_roots(self):
        self.assertEqual([digital_root(x) for x in (0, 1, 3, 6, 9, 18, 27)], [0, 1, 3, 6, 9, 9, 9])
        self.assertAlmostEqual(harmonic_phase(9), 2 * 3.141592653589793)

    def test_hadamard_is_normalized(self):
        state = HarmonicStateVector(1).hadamard(0)
        self.assertAlmostEqual(state.norm_squared(), 1.0)
        self.assertEqual(set(state.measure(100, seed=7)), {"0", "1"})

    def test_bell_pair_correlations(self):
        state = HarmonicStateVector(2).hadamard(0).cnot(0, 1)
        self.assertAlmostEqual(state.norm_squared(), 1.0)
        self.assertEqual(set(state.measure(100, seed=11)), {"00", "11"})

    def test_phase_preserves_norm(self):
        state = HarmonicStateVector(2).hadamard(0).hadamard(1).harmonic_phase(0, 6)
        self.assertAlmostEqual(state.norm_squared(), 1.0)

    def test_rejects_bad_qubits(self):
        with self.assertRaises(ValueError):
            HarmonicStateVector(0)
        with self.assertRaises(ValueError):
            HarmonicStateVector(1).hadamard(1)

if __name__ == "__main__":
    unittest.main()