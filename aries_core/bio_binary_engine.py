"""Experimental ARIES frequency-modulated attention layer.

This module is an experimental research component, not a proven physical law,
mathematical breakthrough, or drop-in replacement for Hugging Face GPT-2 attention.
It is not wired into the published GPT-2-style model unless a separate model
integration explicitly imports and installs this layer.
"""
from __future__ import annotations

import math
import torch
import torch.nn as nn


class BioBinaryFrequencyAttention(nn.Module):
    """Multi-head self-attention with a bounded sinusoidal score modulation.

    Inputs have shape [batch, sequence, embed_dim]. By default the layer is
    causal, so token positions cannot attend to future positions. An optional
    attention mask may be [batch, sequence], [batch, query, key], or
    [batch, 1, query, key], where nonzero means allowed.
    """

    def __init__(self, embed_dim: int, num_heads: int, *, causal: bool = True):
        super().__init__()
        if embed_dim <= 0 or num_heads <= 0:
            raise ValueError("embed_dim and num_heads must be positive")
        if embed_dim % num_heads:
            raise ValueError("embed_dim must be divisible by num_heads")
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads
        self.causal = causal

        self.register_buffer(
            "frequency_nodes", torch.tensor([3.0, 6.0, 9.0], dtype=torch.float32)
        )
        self.q_proj = nn.Linear(embed_dim, embed_dim)
        self.k_proj = nn.Linear(embed_dim, embed_dim)
        self.v_proj = nn.Linear(embed_dim, embed_dim)
        self.out_proj = nn.Linear(embed_dim, embed_dim)

    def forward(self, x: torch.Tensor, mask: torch.Tensor | None = None) -> torch.Tensor:
        if x.ndim != 3:
            raise ValueError("x must have shape [batch, sequence, embed_dim]")
        batch_size, seq_len, width = x.shape
        if width != self.embed_dim:
            raise ValueError(f"expected final dimension {self.embed_dim}, got {width}")
        if seq_len == 0:
            return x

        def split_heads(proj: nn.Linear) -> torch.Tensor:
            return proj(x).reshape(
                batch_size, seq_len, self.num_heads, self.head_dim
            ).transpose(1, 2)

        q, k, v = split_heads(self.q_proj), split_heads(self.k_proj), split_heads(self.v_proj)
        scores = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(self.head_dim)

        # Bounded modulation; the coefficient is a design choice, not a proven invariant.
        freq = self.frequency_nodes.to(dtype=scores.dtype, device=scores.device)
        scores = scores + torch.sin(scores * (freq[0] / freq[2])) * 0.1

        allowed = None
        if self.causal:
            allowed = torch.ones(seq_len, seq_len, dtype=torch.bool, device=x.device).tril()
            allowed = allowed.view(1, 1, seq_len, seq_len)

        if mask is not None:
            mask = mask.to(device=x.device)
            if mask.ndim == 2:
                if mask.shape != (batch_size, seq_len):
                    raise ValueError("2D mask must have shape [batch, sequence]")
                # Token-validity mask: keys with zero are hidden.
                key_allowed = mask[:, None, None, :].bool()
            elif mask.ndim == 3:
                if mask.shape != (batch_size, seq_len, seq_len):
                    raise ValueError("3D mask must have shape [batch, query, key]")
                key_allowed = mask[:, None, :, :].bool()
            elif mask.ndim == 4:
                if mask.shape[0] not in (1, batch_size) or mask.shape[-2:] != (seq_len, seq_len):
                    raise ValueError("4D mask must broadcast to [batch, heads, query, key]")
                key_allowed = mask.bool()
            else:
                raise ValueError("mask must be 2D, 3D, or 4D")
            allowed = key_allowed if allowed is None else (allowed & key_allowed)

        if allowed is not None:
            scores = scores.masked_fill(~allowed, torch.finfo(scores.dtype).min)

        weights = torch.softmax(scores, dim=-1)
        context = torch.matmul(weights, v)
        context = context.transpose(1, 2).contiguous().reshape(batch_size, seq_len, self.embed_dim)
        return self.out_proj(context)
