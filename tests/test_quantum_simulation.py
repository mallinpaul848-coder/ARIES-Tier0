import unittest

from aries_math.quantum_simulation import (
    zero_state, hadamard, pauli_x, cnot, probabilities, measure,
)


class QuantumSimulationTests(unittest.TestCase):
    def test_zero_state_is_normalized(self):
        self.assertEqual(probabilities(zero_state(2)), [1.0, 0.0, 0.0, 0.0])

    def test_pauli_x_flips_basis_state(self):
        self.assertEqual(probabilities(pauli_x(zero_state(1), 0)), [0.0, 1.0])

    def test_hadamard_creates_equal_probabilities(self):
        p = probabilities(hadamard(zero_state(1), 0))
        self.assertAlmostEqual(p[0], 0.5)
        self.assertAlmostEqual(p[1], 0.5)

    def test_bell_pair_correlated_measurements(self):
        state = cnot(hadamard(zero_state(2), 0), control=0, target=1)
        p = probabilities(state)
        self.assertAlmostEqual(p[0], 0.5)
        self.assertAlmostEqual(p[3], 0.5)
        self.assertAlmostEqual(p[1], 0.0)
        self.assertAlmostEqual(p[2], 0.0)
        outcomes = measure(state, shots=100, seed=7)
        self.assertTrue(set(outcomes).issubset({"00", "11"}))
        self.assertGreater(len(set(outcomes)), 1)

    def test_measurement_is_reproducible(self):
        state = hadamard(zero_state(1), 0)
        self.assertEqual(measure(state, 50, 123), measure(state, 50, 123))

    def test_invalid_inputs_are_rejected(self):
        with self.assertRaises(ValueError):
            zero_state(0)
        with self.assertRaises(ValueError):
            probabilities([1, 1])
        with self.assertRaises(ValueError):
            hadamard(zero_state(1), 1)


if __name__ == "__main__":
    unittest.main()
