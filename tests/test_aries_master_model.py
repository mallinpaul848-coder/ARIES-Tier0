"""Small deterministic tests for the experimental ARIES Transformer."""
import unittest

try:
    import torch
    from aries_math.aries_master_model import AriesMasterModel, count_parameters
except ImportError:
    torch = None
    AriesMasterModel = None
    count_parameters = None


@unittest.skipIf(torch is None, "PyTorch is optional; install torch to run model tests")
class TestAriesMasterModel(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(7)
        self.model = AriesMasterModel(
            vocab_size=32, d_model=16, n_layers=2, n_heads=4, max_seq_len=12, dropout=0
        )

    def test_logits_shape_and_finite_loss(self):
        ids = torch.randint(0, 32, (2, 8))
        result = self.model(ids, labels=ids)
        self.assertEqual(tuple(result["logits"].shape), (2, 8, 32))
        self.assertTrue(torch.isfinite(result["loss"]).item())

    def test_causal_mask_prevents_future_token_leak(self):
        self.model.eval()
        a = torch.tensor([[1, 2, 3, 4]])
        b = torch.tensor([[1, 2, 9, 8]])
        with torch.no_grad():
            logits_a = self.model(a)["logits"]
            logits_b = self.model(b)["logits"]
        self.assertTrue(torch.allclose(logits_a[:, :2], logits_b[:, :2], atol=1e-6))

    def test_generation_length_and_greedy_repeatability(self):
        ids = torch.tensor([[1, 2, 3]])
        first = self.model.generate(ids, max_new_tokens=3, temperature=0)
        second = self.model.generate(ids, max_new_tokens=3, temperature=0)
        self.assertEqual(tuple(first.shape), (1, 6))
        self.assertTrue(torch.equal(first, second))

    def test_rejects_too_long_context(self):
        with self.assertRaises(ValueError):
            self.model(torch.ones((1, 13), dtype=torch.long))

    def test_parameter_count_positive(self):
        self.assertGreater(count_parameters(self.model), 0)


if __name__ == "__main__":
    unittest.main()
