"""Optional tests for the experimental ARIES causal Transformer.

Run after installing requirements-experimental.txt:
    python -m unittest discover -s experiments -p "test_*.py" -v
"""
import unittest

try:
    import torch
except ImportError:  # Keep production test environments independent of PyTorch.
    torch = None

if torch is not None:
    from aries_master_model import AriesCausalLM, sample_batch


@unittest.skipIf(torch is None, "install requirements-experimental.txt to run optional tests")
class AriesCausalLMTests(unittest.TestCase):
    def test_forward_shape(self):
        model = AriesCausalLM(d_model=32, n_layers=2, n_heads=4, max_seq_len=16)
        logits = model(torch.randint(0, 256, (2, 8)))
        self.assertEqual(tuple(logits.shape), (2, 8, 256))

    def test_causal_attention_does_not_leak_future_bytes(self):
        torch.manual_seed(1)
        model = AriesCausalLM(d_model=32, n_layers=2, n_heads=4, max_seq_len=16, dropout=0.0)
        model.eval()
        first = torch.tensor([[1, 2, 3, 4]])
        changed_future = torch.tensor([[1, 2, 200, 201]])
        with torch.inference_mode():
            a = model(first)
            b = model(changed_future)
        self.assertTrue(torch.allclose(a[:, :2, :], b[:, :2, :], atol=1e-6, rtol=1e-5))

    def test_sample_batch_shifts_next_byte_targets(self):
        data = torch.arange(20, dtype=torch.long)
        x, y = sample_batch(data, batch_size=4, seq_len=5, device=torch.device("cpu"))
        self.assertEqual(tuple(x.shape), (4, 5))
        self.assertTrue(torch.equal(y[:, :-1], x[:, 1:]))
        self.assertTrue(torch.equal(y[:, 0], x[:, 0] + 1))


if __name__ == "__main__":
    unittest.main()
