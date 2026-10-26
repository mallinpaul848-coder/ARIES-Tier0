import unittest

from aries_math.learning_system import (
    DEFAULT_SUBJECTS, KnowledgeLibrary, KnowledgeRecord, record_id,
)


def sample_record(**kwargs):
    values = dict(
        title="Fractions and ratios",
        subject="mathematics",
        content="A fraction represents part of a whole.",
        source_name="Example textbook",
        source_url="https://example.org/math/fractions",
        evidence_level="textbook",
        reviewed=True,
        tags=("fractions", "ratio"),
    )
    values.update(kwargs)
    return KnowledgeRecord(**values)


class LearningSystemTests(unittest.TestCase):
    def test_subject_catalog_covers_multiple_domains(self):
        self.assertGreaterEqual(len(DEFAULT_SUBJECTS), 15)
        self.assertIn("medicine_health", DEFAULT_SUBJECTS)
        self.assertIn("language_grammar", DEFAULT_SUBJECTS)

    def test_add_search_and_provenance(self):
        lib = KnowledgeLibrary()
        rid = lib.add(sample_record())
        result = lib.search("fraction whole", subject="mathematics")
        self.assertEqual(result[0]["record_id"], rid)
        self.assertEqual(result[0]["source_url"], "https://example.org/math/fractions")
        self.assertTrue(result[0]["should_be_cited"])
        self.assertTrue(result[0]["reviewed"])

    def test_duplicate_records_are_idempotent(self):
        lib = KnowledgeLibrary()
        self.assertEqual(lib.add(sample_record()), lib.add(sample_record()))
        self.assertEqual(lib.subject_coverage()["record_count"], 1)

    def test_unknown_subject_requires_registration(self):
        lib = KnowledgeLibrary()
        with self.assertRaises(ValueError):
            lib.add(sample_record(subject="astrophysics"))
        lib.register_subject("astrophysics")
        self.assertEqual(lib.add(sample_record(subject="astrophysics")), record_id(sample_record(subject="astrophysics")))

    def test_invalid_source_rejected(self):
        with self.assertRaises(ValueError):
            sample_record(source_url="not-a-url")

    def test_feedback_creates_review_proposal_not_auto_change(self):
        lib = KnowledgeLibrary()
        lib.record_feedback("reasoning-01", "fail", "confused conditionals")
        proposal = lib.improvement_proposals()[0]
        self.assertFalse(proposal["automatic_code_change"])
        self.assertFalse(proposal["automatic_weight_update"])
        self.assertEqual(proposal["task_id"], "reasoning-01")

    def test_feedback_validates_outcome(self):
        with self.assertRaises(ValueError):
            KnowledgeLibrary().record_feedback("x", "maybe")

    def test_empty_query_rejected(self):
        with self.assertRaises(ValueError):
            KnowledgeLibrary().search(" ")

    def test_coverage_does_not_claim_mastery(self):
        self.assertTrue(KnowledgeLibrary().subject_coverage()["coverage_is_not_mastery"])


if __name__ == "__main__":
    unittest.main()
