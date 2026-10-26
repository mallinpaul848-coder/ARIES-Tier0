import unittest
from aries_math.double_helix_scheduler import Candidate, DoubleHelixScheduler

class DoubleHelixSchedulerTests(unittest.TestCase):
    def test_keeps_validated_baseline_when_candidate_not_validated(self):
        s = DoubleHelixScheduler(100)
        s.register(Candidate("baseline", "software", lambda x: x, validated=True))
        s.register(Candidate("unverified", "hardware", lambda x: x, validated=False))
        s.benchmark("baseline", "payload", 3)
        self.assertEqual(s.choose("baseline").name, "baseline")

    def test_selects_measured_faster_validated_candidate(self):
        s = DoubleHelixScheduler(100)
        s.register(Candidate("baseline", "software", lambda x: sum(range(1000)), validated=True))
        s.register(Candidate("candidate", "hardware", lambda x: x, validated=True))
        s.benchmark("baseline", None, 3)
        s.benchmark("candidate", None, 3)
        self.assertEqual(s.choose("baseline").name, "candidate")

    def test_requires_repeated_measurements(self):
        s = DoubleHelixScheduler(100)
        s.register(Candidate("baseline", "software", lambda x: x, validated=True))
        with self.assertRaises(ValueError): s.benchmark("baseline", None, 1)

    def test_quantum_device_requirement_is_explicit(self):
        s = DoubleHelixScheduler(100, quantum_available=False)
        s.register(Candidate("qpu", "hardware", lambda x: x, validated=True, requires_quantum_device=True))
        with self.assertRaises(RuntimeError): s.benchmark("qpu", None, 3)

if __name__ == "__main__": unittest.main()