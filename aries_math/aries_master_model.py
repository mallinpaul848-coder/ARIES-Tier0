"""Experimental ARIES decoder-only Transformer prototype.

This research module is separate from the production native n-gram API. It is
not pretrained and does not prove P=NP, sub-nanosecond inference, or trillion-
token training. Train it only with real tokenized data and adequate compute.
"""
from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


class AriesHarmonicEmbedding(nn.Module):
    """Token + position embeddings with a bounded optional 3/6/9-inspired gate."""

    def __init__(self, vocab_size: int, d_model: int, max_seq_len: int,
                 harmonic_gate: bool = True, dropout: float = 0.1):
        super().__init__()
        self.token = nn.Embedding(vocab_size, d_model)
        self.position = nn.Embedding(max_seq_len, d_model)
        self.harmonic_gate = harmonic_gate
        pattern = torch.tensor([1.00, 1.02, 0.98]).repeat((d_model + 2) // 3)[:d_model]
        self.register_buffer("feature_gate", pattern.view(1, 1, d_model), persistent=False)
        self.dropout = nn.Dropout(dropout)

    def forward(self, input_ids: torch.Tensor) -> torch.Tensor:
        seq_len = input_ids.size(1)
        positions = torch.arange(seq_len, device=input_ids.device).unsqueeze(0)
        x = self.token(input_ids) + self.position(positions)
        if self.harmonic_gate:
            x = x * self.feature_gate
        return self.dropout(x)


class AriesDecoderBlock(nn.Module):
    """Pre-norm decoder block; causal mask prevents looking at future tokens."""

    def __init__(self, d_model: int, n_heads: int, dropout: float = 0.1):
        super().__init__()
        if d_model % n_heads:
            raise ValueError("d_model must be divisible by n_heads")
        self.norm1 = nn.LayerNorm(d_model)
        self.attn = nn.MultiheadAttention(d_model, n_heads, dropout=dropout, batch_first=True)
        self.norm2 = nn.LayerNorm(d_model)
        self.ff = nn.Sequential(
            nn.Linear(d_model, 4 * d_model),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(4 * d_model, d_model),
            nn.Dropout(dropout),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        seq_len = x.size(1)
        mask = torch.triu(
            torch.ones(seq_len, seq_len, dtype=torch.bool, device=x.device), diagonal=1
        )
        normalized = self.norm1(x)
        attended, _ = self.attn(
            normalized, normalized, normalized, attn_mask=mask, need_weights=False
        )
        x = x + attended
        return x + self.ff(self.norm2(x))


class AriesMasterModel(nn.Module):
    """Configurable decoder-only language model trained by next-token prediction."""

    def __init__(self, vocab_size: int = 32000, d_model: int = 256,
                 n_layers: int = 4, n_heads: int = 8, max_seq_len: int = 512,
                 dropout: float = 0.1, harmonic_gate: bool = True):
        super().__init__()
        if min(vocab_size, d_model, n_layers, n_heads, max_seq_len) <= 0:
            raise ValueError("all model dimensions must be positive")
        if d_model % n_heads:
            raise ValueError("d_model must be divisible by n_heads")
        self.vocab_size = vocab_size
        self.max_seq_len = max_seq_len
        self.embedding = AriesHarmonicEmbedding(
            vocab_size, d_model, max_seq_len, harmonic_gate, dropout
        )
        self.blocks = nn.ModuleList([
            AriesDecoderBlock(d_model, n_heads, dropout) for _ in range(n_layers)
        ])
        self.norm = nn.LayerNorm(d_model)
        self.lm_head = nn.Linear(d_model, vocab_size, bias=False)
        # Weight tying reduces parameters and is standard for small language models.
        self.lm_head.weight = self.embedding.token.weight

    def forward(self, input_ids: torch.Tensor,
                labels: torch.Tensor | None = None) -> dict[str, torch.Tensor | None]:
        if input_ids.ndim != 2:
            raise ValueError("input_ids must have shape [batch, sequence]")
        if input_ids.size(1) == 0 or input_ids.size(1) > self.max_seq_len:
            raise ValueError(f"sequence length must be between 1 and {self.max_seq_len}")
        if input_ids.min().item() < 0 or input_ids.max().item() >= self.vocab_size:
            raise ValueError("input token ID is outside the configured vocabulary")
        x = self.embedding(input_ids)
        for block in self.blocks:
            x = block(x)
        logits = self.lm_head(self.norm(x))
        loss = None
        if labels is not None:
            if labels.shape != input_ids.shape:
                raise ValueError("labels must have the same shape as input_ids")
            if input_ids.size(1) < 2:
                raise ValueError("at least two tokens are needed for next-token loss")
            loss = F.cross_entropy(
                logits[:, :-1, :].contiguous().view(-1, self.vocab_size),
                labels[:, 1:].contiguous().view(-1),
            )
        return {"logits": logits, "loss": loss}

    @torch.no_grad()
    def generate(self, input_ids: torch.Tensor, max_new_tokens: int = 32,
                 temperature: float = 1.0, top_k: int | None = 50) -> torch.Tensor:
        """Greedy or temperature sampling generation, with context safely cropped."""
        if max_new_tokens < 0:
            raise ValueError("max_new_tokens must be non-negative")
        if temperature < 0:
            raise ValueError("temperature must be non-negative")
        if input_ids.ndim != 2 or input_ids.size(1) == 0:
            raise ValueError("input_ids must be non-empty [batch, sequence]")
        was_training = self.training
        self.eval()
        try:
            result = input_ids
            for _ in range(max_new_tokens):
                context = result[:, -self.max_seq_len:]
                logits = self(context)["logits"][:, -1, :]
                if temperature == 0:
                    next_token = logits.argmax(dim=-1, keepdim=True)
                else:
                    logits = logits / temperature
                    if top_k is not None and 0 < top_k < logits.size(-1):
                        cutoff = torch.topk(logits, top_k, dim=-1).values[:, -1, None]
                        logits = logits.masked_fill(logits < cutoff, float("-inf"))
                    probs = torch.softmax(logits, dim=-1)
                    next_token = torch.multinomial(probs, num_samples=1)
                result = torch.cat((result, next_token), dim=1)
            return result
        finally:
            self.train(was_training)


def count_parameters(model: nn.Module) -> int:
    """Count trainable parameters without estimating performance."""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)
