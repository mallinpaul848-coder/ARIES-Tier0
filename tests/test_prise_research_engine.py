import unittest
from aries_math.prise_research_engine import ARIESPRISEResearchEngine, DigitalRootSystem, PRISEProfile, ProofObligation, helixo_features, phase8, vortex369

class TestPRISEResearchMath(unittest.TestCase):
    def test_digital_root(self):
        self.assertEqual(DigitalRootSystem.compute(0), 0)
        self.assertEqual(DigitalRootSystem.compute(18), 9)
        self.assertEqual(DigitalRootSystem.compute(-19), 1)
    def test_vortex_cycle(self):
        self.assertEqual([vortex369(i) for i in range(1,7)], [1,2,4,8,7,5])
        self.assertEqual(vortex369(0), 0)
    def test_phase8(self):
        self.assertIsNone(phase8(0,0)["phase"])
        self.assertEqual(phase8(1,0)["phase"], 0)
        self.assertEqual(phase8(0,1)["phase"], 2)
    def test_helixo(self):
        self.assertEqual(helixo_features([])["count"], 0)
        self.assertEqual(helixo_features([3,4])["energy"], 25.0)
    def test_prise_validation(self):
        with self.assertRaises(ValueError): PRISEProfile(priority=-1).score()
    def test_deterministic_and_cautious(self):
        engine = ARIESPRISEResearchEngine()
        a, b = engine.analyze("P vs NP",[3,6,9]), engine.analyze("P vs NP",[3,6,9])
        self.assertEqual(a["fingerprint_sha256"], b["fingerprint_sha256"])
        self.assertFalse(a["proof_claim"])
        self.assertIn("SAT", a["route"])
    def test_p_vs_np_analysis_exposes_polynomial_sat_compression_obligations(self):
        result = ARIESPRISEResearchEngine().analyze("P vs NP", [3, 6, 9])
        target = result["research_targets"]["sat_compression_obligations"]
        self.assertIn("phi in SAT iff G(E(phi)) == 1", target["equivalence"])
        self.assertIn("q3_q6_q9_test", target)
        self.assertFalse(target["proof_claim"])
        self.assertEqual(target["status"], "open_research_obligations")

    def test_verified_requires_evidence(self):
        item = ProofObligation("P != NP","formal proof")
        with self.assertRaises(ValueError): item.update("verified")

if __name__ == "__main__": unittest.main()
