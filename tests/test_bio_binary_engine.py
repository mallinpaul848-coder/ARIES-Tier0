import pytest
import torch

from aries_core.bio_binary_engine import BioBinaryFrequencyAttention


def test_attention_preserves_shape_and_finite_values():
    layer = BioBinaryFrequencyAttention(48, 6)
    x = torch.randn(2, 7, 48)
    y = layer(x)
    assert y.shape == x.shape
    assert torch.isfinite(y).all()


def test_attention_accepts_padding_mask():
    layer = BioBinaryFrequencyAttention(48, 6)
    x = torch.randn(2, 7, 48)
    mask = torch.ones(2, 7, dtype=torch.long)
    mask[1, -2:] = 0
    y = layer(x, mask=mask)
    assert y.shape == x.shape
    assert torch.isfinite(y).all()


def test_attention_rejects_nondivisible_dimensions():
    with pytest.raises(ValueError, match="divisible"):
        BioBinaryFrequencyAttention(47, 6)


def test_attention_rejects_wrong_input_width():
    layer = BioBinaryFrequencyAttention(48, 6)
    with pytest.raises(ValueError, match="expected final dimension"):
        layer(torch.randn(2, 7, 24))
