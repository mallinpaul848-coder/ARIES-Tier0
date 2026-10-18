#!/usr/bin/env python3
"""Experimental ARIES byte-level causal language model (PyTorch).

This is an optional research module, separate from ARIES's production API.
It trains only on the text file supplied by the operator. It does not simulate
trillions of tokens, prove P=NP, or guarantee sub-nanosecond inference.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import time
from pathlib import Path
from typing import Any

import torch
from torch import nn
from torch.nn import functional as F


class AriesCausalLM(nn.Module):
    """Small byte-level decoder-only Transformer with causal self-attention."""

    def __init__(
        self,
        vocab_size: int = 256,
        d_model: int = 256,
        n_layers: int = 4,
        n_heads: int = 8,
        max_seq_len: int = 256,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        if d_model <= 0 or n_layers <= 0 or n_heads <= 0:
            raise ValueError("d_model, n_layers, and n_heads must be positive")
        if d_model % n_heads:
            raise ValueError("d_model must be divisible by n_heads")
        if max_seq_len < 2:
            raise ValueError("max_seq_len must be at least 2")
        if not 0.0 <= dropout < 1.0:
            raise ValueError("dropout must be in [0, 1)")

        self.vocab_size = vocab_size
        self.d_model = d_model
        self.max_seq_len = max_seq_len
        self.token_embedding = nn.Embedding(vocab_size, d_model)
        self.position_embedding = nn.Embedding(max_seq_len, d_model)
        layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=n_heads,
            dim_feedforward=4 * d_model,
            dropout=dropout,
            activation="gelu",
            batch_first=True,
            norm_first=True,
        )
        self.blocks = nn.TransformerEncoder(layer, num_layers=n_layers)
        self.final_norm = nn.LayerNorm(d_model)
        self.lm_head = nn.Linear(d_model, vocab_size, bias=False)
        self.lm_head.weight = self.token_embedding.weight
        self.register_buffer(
            "causal_mask",
            torch.triu(torch.ones(max_seq_len, max_seq_len, dtype=torch.bool), diagonal=1),
            persistent=False,
        )
        self.apply(self._init_weights)

    @staticmethod
    def _init_weights(module: nn.Module) -> None:
        if isinstance(module, (nn.Linear, nn.Embedding)):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if isinstance(module, nn.Linear) and module.bias is not None:
                nn.init.zeros_(module.bias)

    def forward(self, input_ids: torch.Tensor) -> torch.Tensor:
        if input_ids.ndim != 2:
            raise ValueError("input_ids must have shape [batch, sequence]")
        batch_size, seq_len = input_ids.shape
        if seq_len < 1 or seq_len > self.max_seq_len:
            raise ValueError(f"sequence length must be between 1 and {self.max_seq_len}")
        if input_ids.dtype != torch.long:
            input_ids = input_ids.long()
        positions = torch.arange(seq_len, device=input_ids.device)
        hidden = self.token_embedding(input_ids) * math.sqrt(self.d_model)
        hidden = hidden + self.position_embedding(positions).unsqueeze(0)
        hidden = self.blocks(
            hidden,
            mask=self.causal_mask[:seq_len, :seq_len],
        )
        return self.lm_head(self.final_norm(hidden))

    @torch.inference_mode()
    def generate(
        self,
        input_ids: torch.Tensor,
        max_new_tokens: int = 100,
        temperature: float = 0.8,
        top_k: int = 40,
    ) -> torch.Tensor:
        if max_new_tokens < 0:
            raise ValueError("max_new_tokens cannot be negative")
        if temperature <= 0:
            raise ValueError("temperature must be greater than zero")
        if top_k < 1:
            raise ValueError("top_k must be positive")
        self.eval()
        output = input_ids
        for _ in range(max_new_tokens):
            context = output[:, -self.max_seq_len :]
            logits = self(context)[:, -1, :] / temperature
            k = min(top_k, logits.size(-1))
            values, _ = torch.topk(logits, k)
            logits[logits < values[:, [-1]]] = -float("inf")
            probabilities = F.softmax(logits, dim=-1)
            next_token = torch.multinomial(probabilities, num_samples=1)
            output = torch.cat((output, next_token), dim=1)
        return output


def sample_batch(
    data: torch.Tensor, batch_size: int, seq_len: int, device: torch.device
) -> tuple[torch.Tensor, torch.Tensor]:
    """Sample aligned next-byte input/target sequences from a 1-D byte tensor."""
    if data.numel() <= seq_len:
        raise ValueError("training text must contain more bytes than seq_len")
    starts = torch.randint(0, data.numel() - seq_len, (batch_size,))
    x = torch.stack([data[i : i + seq_len] for i in starts.tolist()])
    y = torch.stack([data[i + 1 : i + seq_len + 1] for i in starts.tolist()])
    return x.to(device), y.to(device)


def train(args: argparse.Namespace) -> dict[str, Any]:
    source = Path(args.text)
    raw = source.read_bytes()
    if len(raw) <= args.seq_len:
        raise ValueError(
            f"Training file has {len(raw)} bytes; it must exceed seq_len={args.seq_len}"
        )
    data = torch.tensor(list(raw), dtype=torch.long)
    device = torch.device(args.device if args.device != "auto" else (
        "cuda" if torch.cuda.is_available() else "cpu"
    ))
    model = AriesCausalLM(
        d_model=args.d_model,
        n_layers=args.layers,
        n_heads=args.heads,
        max_seq_len=args.seq_len,
        dropout=args.dropout,
    ).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr)
    rng = random.Random(args.seed)
    torch.manual_seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)

    model.train()
    losses: list[float] = []
    start = time.perf_counter()
    for step in range(1, args.steps + 1):
        x, y = sample_batch(data, args.batch_size, args.seq_len, device)
        optimizer.zero_grad(set_to_none=True)
        logits = model(x)
        loss = F.cross_entropy(logits.reshape(-1, 256), y.reshape(-1))
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        losses.append(float(loss.detach().cpu()))
        if step == 1 or step % args.log_every == 0 or step == args.steps:
            print(f"step={step}/{args.steps} loss={losses[-1]:.4f}")

    elapsed = time.perf_counter() - start
    checkpoint = Path(args.checkpoint)
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "config": {
                "vocab_size": 256,
                "d_model": args.d_model,
                "n_layers": args.layers,
                "n_heads": args.heads,
                "max_seq_len": args.seq_len,
                "dropout": args.dropout,
                "tokenization": "UTF-8 bytes",
            },
            "training": {
                "source_file": str(source),
                "source_bytes": len(raw),
                "steps": args.steps,
                "batch_size": args.batch_size,
                "seed": args.seed,
                "final_loss": losses[-1],
                "elapsed_seconds": elapsed,
                "bytes_processed_in_sampled_batches": args.steps * args.batch_size * args.seq_len,
            },
        },
        checkpoint,
    )
    report = {
        "status": "completed",
        "device": str(device),
        "source_bytes": len(raw),
        "steps": args.steps,
        "final_training_loss": losses[-1],
        "elapsed_seconds": round(elapsed, 3),
        "checkpoint": str(checkpoint),
        "note": "Training loss is not an independent quality benchmark.",
    }
    report_path = checkpoint.with_suffix(".report.json")
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--text", required=True, help="UTF-8 text corpus file to train on")
    parser.add_argument("--checkpoint", default="checkpoints/aries-byte-lm.pt")
    parser.add_argument("--steps", type=int, default=500)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--seq-len", type=int, default=128)
    parser.add_argument("--d-model", type=int, default=128)
    parser.add_argument("--layers", type=int, default=4)
    parser.add_argument("--heads", type=int, default=4)
    parser.add_argument("--dropout", type=float, default=0.1)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--log-every", type=int, default=50)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.steps < 1 or args.batch_size < 1 or args.seq_len < 2 or args.log_every < 1:
        raise SystemExit("steps/log-every/batch-size must be positive and seq-len >= 2")
    if args.device == "cuda" and not torch.cuda.is_available():
        raise SystemExit("CUDA was requested but is not available")
    train(args)


if __name__ == "__main__":
    main()
