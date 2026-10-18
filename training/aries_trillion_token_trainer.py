#!/usr/bin/env python3
"""ARIES streaming causal-language-model trainer.

This is a training harness, not proof that ARIES has consumed a trillion tokens.
The safe default is a 3-step smoke run. Use --max-steps 0 to keep training until
--target-training-tokens is reached, on hardware and data sized for the job.

Tokenizer modes:
  byte       Offline UTF-8 byte tokenizer (IDs 0..255 plus end-of-line ID 256).
             Counts are byte-token exposures, not GPT/BPE token counts.
  hf:NAME    Use a Hugging Face tokenizer, e.g. hf:gpt2. Install transformers and
             tokenizers first; counts use that tokenizer's token IDs.

Example:
  python training/aries_trillion_token_trainer.py --corpus data/licensed.txt
  torchrun --nproc_per_node=2 training/aries_trillion_token_trainer.py \\
      --corpus data/licensed.txt --tokenizer hf:gpt2 --max-steps 10000

The 3-6-9 feature is a small experimental embedding modulation. The projection
layer is ordinary learned neural-network math; it does not solve P=NP.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
import time
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", required=True, help="UTF-8 text corpus you own or are licensed to use")
    parser.add_argument("--tokenizer", default="byte", help="byte (offline) or hf:tokenizer-name (e.g. hf:gpt2)")
    parser.add_argument("--output-dir", default="artifacts/aries-streaming-trainer")
    parser.add_argument("--target-training-tokens", type=int, default=1_000_000_000_000,
                        help="Cumulative target-token exposures across all workers; target, not a completion claim")
    parser.add_argument("--max-steps", type=int, default=3,
                        help="Maximum additional optimizer steps; use 0 to run until token target is reached")
    parser.add_argument("--checkpoint-every-steps", type=int, default=100)
    parser.add_argument("--resume-from-checkpoint", default="",
                        help="Checkpoint path, or 'latest' to resume output-dir/checkpoint.pt")
    parser.add_argument("--batch-size", type=int, default=2, help="Per-process batch size")
    parser.add_argument("--seq-len", type=int, default=128)
    parser.add_argument("--d-model", type=int, default=128)
    parser.add_argument("--layers", type=int, default=4)
    parser.add_argument("--heads", type=int, default=4)
    parser.add_argument("--dropout", type=float, default=0.1)
    parser.add_argument("--learning-rate", type=float, default=3e-4)
    parser.add_argument("--weight-decay", type=float, default=0.01)
    parser.add_argument("--seed", type=int, default=369)
    parser.add_argument("--no-amp", action="store_true", help="Disable CUDA mixed precision")
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def load_tokenizer(mode: str):
    if mode == "byte":
        return None, 257, 256, "utf8_byte_ids_plus_eol_v1"
    if not mode.startswith("hf:") or not mode[3:].strip():
        raise ValueError("--tokenizer must be 'byte' or 'hf:NAME'")
    try:
        from transformers import AutoTokenizer
    except ImportError as exc:
        raise RuntimeError("HF tokenizer mode requires: python -m pip install transformers tokenizers") from exc
    tokenizer_name = mode[3:].strip()
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_name, use_fast=True)
    if tokenizer.eos_token_id is None:
        raise ValueError(f"Tokenizer {tokenizer_name!r} has no EOS token; choose a tokenizer that defines one.")
    return tokenizer, len(tokenizer), int(tokenizer.eos_token_id), tokenizer_name


def build_dataset(torch, corpus: Path, tokenizer, tokenizer_mode: str, eos_id: int,
                  seq_len: int, rank: int, world_size: int):
    class StreamingTokenBlocks(torch.utils.data.IterableDataset):
        def __iter__(self):
            buffer: list[int] = []
            line_index = 0
            binary_mode = tokenizer_mode == "byte"
            open_kwargs = {} if binary_mode else {"encoding": "utf-8-sig", "errors": "replace"}
            with corpus.open("rb" if binary_mode else "r", **open_kwargs) as handle:
                for line in handle:
                    current_line = line_index
                    line_index += 1
                    if current_line % world_size != rank:
                        continue
                    if binary_mode:
                        token_ids = list(line)
                        token_ids.append(eos_id)
                    else:
                        token_ids = tokenizer.encode(line, add_special_tokens=False)
                        if token_ids:
                            token_ids.append(eos_id)
                    if not token_ids:
                        continue
                    buffer.extend(int(token_id) for token_id in token_ids)
                    while len(buffer) >= seq_len + 1:
                        block = buffer[:seq_len + 1]
                        # Keep the final context token to predict the next block's first target.
                        del buffer[:seq_len]
                        values = torch.tensor(block, dtype=torch.long)
                        yield values[:-1], values[1:]
    return StreamingTokenBlocks()


def build_model(torch, nn, functional, vocab_size: int, d_model: int, layers: int,
                heads: int, seq_len: int, dropout: float):
    class HarmonicEmbedding(nn.Module):
        def __init__(self):
            super().__init__()
            self.tokens = nn.Embedding(vocab_size, d_model)
            self.positions = nn.Embedding(seq_len, d_model)
            # Small, mean-one modulation keeps the experimental 3/6/9 pattern bounded.
            pattern = torch.tensor([0.95, 1.0, 1.05], dtype=torch.float32)
            scale = pattern[torch.arange(d_model) % 3]
            self.register_buffer("harmonic_scale", scale.view(1, 1, d_model), persistent=False)

        def forward(self, input_ids):
            positions = torch.arange(input_ids.shape[1], device=input_ids.device).unsqueeze(0)
            return self.tokens(input_ids) * self.harmonic_scale + self.positions(positions)

    class CausalSelfAttention(nn.Module):
        def __init__(self):
            super().__init__()
            if d_model % heads:
                raise ValueError("d-model must be divisible by heads")
            self.heads = heads
            self.head_dim = d_model // heads
            self.qkv = nn.Linear(d_model, 3 * d_model)
            self.out = nn.Linear(d_model, d_model)
            self.attn_dropout = dropout
            self.resid_dropout = nn.Dropout(dropout)

        def forward(self, x):
            batch, length, width = x.shape
            qkv = self.qkv(x).view(batch, length, 3, self.heads, self.head_dim).permute(2, 0, 3, 1, 4)
            q, k, v = qkv.unbind(0)
            context = functional.scaled_dot_product_attention(
                q, k, v,
                dropout_p=self.attn_dropout if self.training else 0.0,
                is_causal=True,
            )
            context = context.transpose(1, 2).contiguous().view(batch, length, width)
            return self.resid_dropout(self.out(context))

    class HarmonicProjection(nn.Module):
        """A learned residual projection; it is not a P=NP reduction or proof."""
        def __init__(self):
            super().__init__()
            self.projection = nn.Linear(d_model, d_model)
            self.bias = nn.Parameter(torch.zeros(d_model))

        def forward(self, x):
            return functional.gelu(self.projection(x) + self.bias)

    class TransformerBlock(nn.Module):
        def __init__(self):
            super().__init__()
            self.norm1 = nn.LayerNorm(d_model)
            self.norm2 = nn.LayerNorm(d_model)
            self.norm3 = nn.LayerNorm(d_model)
            self.attention = CausalSelfAttention()
            self.projection = HarmonicProjection()
            self.ffn = nn.Sequential(
                nn.Linear(d_model, 4 * d_model),
                nn.GELU(),
                nn.Linear(4 * d_model, d_model),
                nn.Dropout(dropout),
            )

        def forward(self, x):
            x = x + self.attention(self.norm1(x))
            x = x + self.projection(self.norm2(x))
            x = x + self.ffn(self.norm3(x))
            return x

    class AriesCausalLM(nn.Module):
        def __init__(self):
            super().__init__()
            self.embedding = HarmonicEmbedding()
            self.blocks = nn.ModuleList([TransformerBlock() for _ in range(layers)])
            self.norm = nn.LayerNorm(d_model)
            self.lm_head = nn.Linear(d_model, vocab_size, bias=False)
            self.lm_head.weight = self.embedding.tokens.weight

        def forward(self, input_ids):
            x = self.embedding(input_ids)
            for block in self.blocks:
                x = block(x)
            return self.lm_head(self.norm(x))
    return AriesCausalLM()


def main() -> int:
    args = parse_args()
    corpus = Path(args.corpus)
    if not corpus.is_file():
        print(f"ERROR: corpus file not found: {corpus}", file=sys.stderr)
        return 2
    if corpus.stat().st_size == 0:
        print("ERROR: corpus is empty.", file=sys.stderr)
        return 2
    if args.target_training_tokens < 1 or args.max_steps < 0 or args.checkpoint_every_steps < 1:
        print("ERROR: target must be positive, max-steps non-negative, and checkpoint interval positive.", file=sys.stderr)
        return 2
    if args.batch_size < 1 or args.seq_len < 2 or args.d_model < 8 or args.layers < 1 or args.heads < 1:
        print("ERROR: batch-size >=1, seq-len >=2, d-model >=8, layers >=1, and heads >=1 are required.", file=sys.stderr)
        return 2
    if args.d_model % args.heads:
        print("ERROR: d-model must be divisible by heads.", file=sys.stderr)
        return 2
    if not 0.0 <= args.dropout < 1.0 or args.learning_rate <= 0 or args.weight_decay < 0:
        print("ERROR: invalid dropout, learning-rate, or weight-decay value.", file=sys.stderr)
        return 2

    try:
        import torch
        import torch.nn as nn
        import torch.nn.functional as functional
        from torch.utils.data import DataLoader
    except ImportError as exc:
        print(f"ERROR: PyTorch is required. Install with: python -m pip install 'torch>=2.2,<3.0'. Details: {exc}", file=sys.stderr)
        return 2

    try:
        tokenizer, vocab_size, eos_id, tokenizer_label = load_tokenizer(args.tokenizer)
    except (RuntimeError, ValueError, OSError) as exc:
        print(f"ERROR: tokenizer setup failed: {exc}", file=sys.stderr)
        return 2

    world_size = int(os.environ.get("WORLD_SIZE", "1"))
    rank = int(os.environ.get("RANK", "0"))
    local_rank = int(os.environ.get("LOCAL_RANK", "0"))
    distributed = world_size > 1
    if distributed:
        if torch.cuda.is_available():
            torch.cuda.set_device(local_rank)
            device = torch.device("cuda", local_rank)
            backend = "nccl"
        else:
            device = torch.device("cpu")
            backend = "gloo"
        torch.distributed.init_process_group(backend=backend)
    else:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        if device.type == "cuda":
            torch.cuda.set_device(device)

    torch.manual_seed(args.seed)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(args.seed)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = output_dir / "checkpoint.pt"
    evidence_path = output_dir / "training_evidence.json"
    corpus_hash = sha256_file(corpus)
    model_config = {
        "vocab_size": vocab_size, "d_model": args.d_model, "layers": args.layers,
        "heads": args.heads, "seq_len": args.seq_len, "dropout": args.dropout,
        "tokenizer": tokenizer_label,
    }

    model = build_model(torch, nn, functional, vocab_size, args.d_model, args.layers,
                        args.heads, args.seq_len, args.dropout).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate, weight_decay=args.weight_decay)
    start_step = 0
    tokens_seen = 0
    if args.resume_from_checkpoint:
        resume_path = checkpoint_path if args.resume_from_checkpoint == "latest" else Path(args.resume_from_checkpoint)
        if not resume_path.is_file():
            print(f"ERROR: checkpoint not found: {resume_path}", file=sys.stderr)
            if distributed:
                torch.distributed.destroy_process_group()
            return 2
        try:
            state = torch.load(resume_path, map_location=device, weights_only=False)
            if state.get("corpus_sha256") != corpus_hash:
                raise ValueError("corpus SHA-256 does not match checkpoint")
            if state.get("model_config") != model_config:
                raise ValueError("model/tokenizer configuration does not match checkpoint")
            model.load_state_dict(state["model_state_dict"])
            optimizer.load_state_dict(state["optimizer_state_dict"])
            start_step = int(state["global_step"])
            tokens_seen = int(state["tokens_seen"])
        except (OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
            print(f"ERROR: could not safely resume checkpoint: {exc}", file=sys.stderr)
            if distributed:
                torch.distributed.destroy_process_group()
            return 2

    if distributed:
        model = torch.nn.parallel.DistributedDataParallel(
            model, device_ids=[local_rank] if device.type == "cuda" else None
        )

    dataset = build_dataset(torch, corpus, tokenizer, args.tokenizer, eos_id, args.seq_len, rank, world_size)
    loader = DataLoader(dataset, batch_size=args.batch_size, num_workers=0, pin_memory=(device.type == "cuda"))
    iterator = iter(loader)
    amp_enabled = device.type == "cuda" and not args.no_amp
    amp_dtype = torch.bfloat16 if amp_enabled and torch.cuda.is_bf16_supported() else torch.float16
    scaler = torch.cuda.amp.GradScaler(enabled=(amp_enabled and amp_dtype == torch.float16))
    model.train()
    run_started = time.perf_counter()
    run_tokens_start = tokens_seen
    run_steps_start = start_step
    loss_sum = 0.0
    loss_count = 0
    last_checkpoint_step = start_step

    if rank == 0:
        print(f"ARIES streaming trainer | device={device} | tokenizer={tokenizer_label} | vocab={vocab_size}")
        print(f"Target token exposures: {args.target_training_tokens:,} | max additional steps: {args.max_steps or 'until target'}")
        print("Status is reported from measured training batches; configuration alone never marks the target complete.")

    try:
        while tokens_seen < args.target_training_tokens and (args.max_steps == 0 or start_step < run_steps_start + args.max_steps):
            try:
                inputs, targets = next(iterator)
            except StopIteration:
                iterator = iter(loader)
                try:
                    inputs, targets = next(iterator)
                except StopIteration:
                    raise RuntimeError(
                        "The corpus shard has too few tokens for one batch. Add more licensed text, "
                        "reduce --batch-size/--seq-len, or verify that each distributed worker has data."
                    )
            inputs = inputs.to(device, non_blocking=True)
            targets = targets.to(device, non_blocking=True)
            optimizer.zero_grad(set_to_none=True)
            with torch.autocast(device_type=device.type, dtype=amp_dtype, enabled=amp_enabled):
                logits = model(inputs)
                loss = functional.cross_entropy(logits.reshape(-1, vocab_size), targets.reshape(-1))
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            scaler.step(optimizer)
            scaler.update()

            start_step += 1
            tokens_seen += int(targets.numel()) * world_size
            loss_value = float(loss.detach().float().item())
            loss_sum += loss_value
            loss_count += 1
            if rank == 0:
                print(f"step={start_step} loss={loss_value:.5f} tokens_seen={tokens_seen:,}/{args.target_training_tokens:,}", flush=True)

            if rank == 0 and (start_step % args.checkpoint_every_steps == 0):
                base_model = model.module if hasattr(model, "module") else model
                checkpoint = {
                    "format": "aries-streaming-causal-lm-v1",
                    "model_state_dict": base_model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "global_step": start_step,
                    "tokens_seen": tokens_seen,
                    "corpus_sha256": corpus_hash,
                    "model_config": model_config,
                    "training_config": {"batch_size_per_worker": args.batch_size, "learning_rate": args.learning_rate},
                }
                temporary = checkpoint_path.with_suffix(".pt.tmp")
                torch.save(checkpoint, temporary)
                os.replace(temporary, checkpoint_path)
                last_checkpoint_step = start_step
    except RuntimeError as exc:
        if distributed:
            torch.distributed.destroy_process_group()
        print(f"ERROR: training stopped: {exc}", file=sys.stderr)
        return 2

    if distributed:
        torch.distributed.barrier()

    if rank == 0:
        base_model = model.module if hasattr(model, "module") else model
        checkpoint = {
            "format": "aries-streaming-causal-lm-v1",
            "model_state_dict": base_model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "global_step": start_step,
            "tokens_seen": tokens_seen,
            "corpus_sha256": corpus_hash,
            "model_config": model_config,
            "training_config": {"batch_size_per_worker": args.batch_size, "learning_rate": args.learning_rate},
        }
        temporary = checkpoint_path.with_suffix(".pt.tmp")
        torch.save(checkpoint, temporary)
        os.replace(temporary, checkpoint_path)
        elapsed = max(time.perf_counter() - run_started, 1e-9)
        target_reached = tokens_seen >= args.target_training_tokens
        evidence = {
            "format": "aries-training-evidence-v1",
            "status": "TARGET_REACHED" if target_reached else "PARTIAL_TARGET_NOT_REACHED",
            "target_training_tokens": args.target_training_tokens,
            "tokens_seen_cumulative": tokens_seen,
            "tokens_seen_this_run": tokens_seen - run_tokens_start,
            "optimizer_steps_cumulative": start_step,
            "optimizer_steps_this_run": start_step - run_steps_start,
            "mean_training_loss_this_run": (loss_sum / loss_count) if loss_count else None,
            "elapsed_seconds_this_run": round(elapsed, 6),
            "measured_tokens_per_second_this_run": round((tokens_seen - run_tokens_start) / elapsed, 3),
            "corpus_sha256": corpus_hash,
            "corpus_path_recorded": str(corpus),
            "tokenizer": tokenizer_label,
            "token_count_semantics": "UTF-8 byte-token exposures (byte mode)" if args.tokenizer == "byte" else "tokenizer ID exposures; not unique corpus tokens",
            "model_config": model_config,
            "hardware": {
                "platform": platform.platform(),
                "python": platform.python_version(),
                "torch": torch.__version__,
                "device": str(device),
                "device_name": torch.cuda.get_device_name(device) if device.type == "cuda" else platform.processor() or "CPU",
                "distributed_world_size": world_size,
            },
            "checkpoint_path": str(checkpoint_path),
            "checkpoint_sha256": sha256_file(checkpoint_path),
            "scientific_scope": {
                "harmonic_feature": "bounded experimental embedding modulation; benefit not assumed",
                "p_vs_np": "No P=NP proof or polynomial solution to general NP-hard problems is implemented or claimed.",
                "pretraining_claim": "Only tokens_seen_cumulative in this manifest are counted; target value alone is not evidence."
            },
            "limitations": [
                "Corpus token exposures include repeated epochs and are not unique corpus tokens.",
                "A short run is a smoke test, not trillion-token pretraining or evidence of broad model capability.",
                "For distributed runs, each optimizer step counts target positions across all workers."
            ],
        }
        atomic_write_json(evidence_path, evidence)
        print(f"Checkpoint: {checkpoint_path}")
        print(f"Evidence: {evidence_path}")
        print(f"Tokens processed in this run: {tokens_seen - run_tokens_start:,}")
        print(f"Cumulative tokens seen: {tokens_seen:,}")
        print(f"Measured throughput: {evidence['measured_tokens_per_second_this_run']:,.2f} token positions/sec")
        print(f"Training status: {evidence['status']}")
        print("Reminder: the target is not complete unless the measured cumulative count reaches the target.")
    if distributed:
        torch.distributed.destroy_process_group()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
