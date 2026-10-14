#!/usr/bin/env python3
"""Train a small ARIES-owned GPT-2-style causal LM from a local text corpus and publish it.

Important: this does NOT convert the existing ARIES character n-gram JSON file into a
Transformer. It trains a new, small model from randomly initialized weights using the
corpus you provide. Quality and leaderboard eligibility are not guaranteed.

Install:
  python -m pip install -U "torch>=2.2" "transformers>=4.45,<5" "tokenizers>=0.20" "huggingface_hub>=0.26" "safetensors>=0.4"

PowerShell:
  $env:HF_TOKEN = "hf_your_write_token"
  python software/train_and_publish_aries_lm.py --corpus data/training.txt --repo-id YOUR_USERNAME/aries-v1

Use a Hugging Face access token with write permission. Never commit the token.
"""
from __future__ import annotations

import os
import sys
import argparse
from pathlib import Path


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--corpus", required=True, help="UTF-8 text file you own or are licensed to use")
    p.add_argument("--repo-id", required=True, help="Real Hub namespace/repository, e.g. username/aries-v1")
    p.add_argument("--output-dir", default="artifacts/aries-v1")
    p.add_argument("--vocab-size", type=int, default=8000)
    p.add_argument("--block-size", type=int, default=256)
    p.add_argument("--layers", type=int, default=4)
    p.add_argument("--heads", type=int, default=4)
    p.add_argument("--hidden-size", type=int, default=256)
    p.add_argument("--steps", type=int, default=1000)
    p.add_argument("--batch-size", type=int, default=2)
    p.add_argument("--learning-rate", type=float, default=5e-4)
    p.add_argument("--seed", type=int, default=369)
    p.add_argument("--private", action="store_true", help="Create a private repo instead of public")
    p.add_argument("--skip-upload", action="store_true", help="Train/export locally only")
    p.add_argument("--model-name", default="ARIES Experimental Causal LM")
    p.add_argument("--license", default="other", help="Review and set an accurate license identifier")
    return p.parse_args()


def main():
    args = parse_args()
    corpus = Path(args.corpus)
    out = Path(args.output_dir)
    if not corpus.is_file():
        print(f"ERROR: corpus file not found: {corpus}", file=sys.stderr)
        return 2
    text = corpus.read_text(encoding="utf-8-sig").strip()
    if len(text) < 100_000:
        print(
            f"ERROR: corpus has only {len(text):,} characters; this strict training pipeline requires at least 100,000 characters of licensed, diverse text. "
            "The deployment demonstration corpus is not suitable evidence of a properly trained language model.",
            file=sys.stderr,
        )
        return 2
    if args.hidden_size % args.heads:
        print("ERROR: --hidden-size must be divisible by --heads.", file=sys.stderr)
        return 2
    if args.block_size < 32 or args.vocab_size < 256 or args.steps < 1:
        print("ERROR: block-size >=32, vocab-size >=256, and steps >=1 are required.", file=sys.stderr)
        return 2
    token = os.getenv("HF_TOKEN")
    if not args.skip_upload and not token:
        print("ERROR: set HF_TOKEN to a Hugging Face write token; do not hardcode it.", file=sys.stderr)
        return 2

    try:
        import torch
        from tokenizers import Tokenizer, decoders, models, pre_tokenizers, trainers
        from transformers import GPT2Config, GPT2LMHeadModel, PreTrainedTokenizerFast, Trainer, TrainingArguments, set_seed
        from huggingface_hub import HfApi
    except ImportError as exc:
        print(f"ERROR: missing dependency: {exc}. Install the packages listed in this script header.", file=sys.stderr)
        return 2

    set_seed(args.seed)
    out.mkdir(parents=True, exist_ok=True)

    # Train a tokenizer from the corpus, not from placeholder metadata.
    backend = Tokenizer(models.BPE(unk_token="<|unk|>"))
    backend.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
    backend.decoder = decoders.ByteLevel()
    special = ["<|pad|>", "<|unk|>", "<|bos|>", "<|eos|>"]
    tokenizer_trainer = trainers.BpeTrainer(
        vocab_size=args.vocab_size,
        min_frequency=2,
        special_tokens=special,
        initial_alphabet=pre_tokenizers.ByteLevel.alphabet(),
    )
    backend.train([str(corpus)], tokenizer_trainer)
    backend.save(str(out / "tokenizer.json"))
    tokenizer = PreTrainedTokenizerFast(
        tokenizer_file=str(out / "tokenizer.json"),
        pad_token="<|pad|>",
        unk_token="<|unk|>",
        bos_token="<|bos|>",
        eos_token="<|eos|>",
        model_max_length=args.block_size,
    )
    tokenizer.save_pretrained(out)

    ids = tokenizer(text, add_special_tokens=False)["input_ids"]
    if len(ids) < max(args.block_size * 2, 20_000):
        print(
            f"ERROR: corpus yields only {len(ids):,} tokens; need at least {max(args.block_size * 2, 20_000):,} tokens. "
            "Provide a larger licensed corpus before training.",
            file=sys.stderr,
        )
        return 2
    usable = (len(ids) // args.block_size) * args.block_size
    blocks = [ids[i:i + args.block_size] for i in range(0, usable, args.block_size)]
    if len(blocks) < 2:
        print("ERROR: need at least two training blocks.", file=sys.stderr)
        return 2

    class PackedDataset(torch.utils.data.Dataset):
        def __len__(self):
            return len(blocks)

        def __getitem__(self, index):
            values = torch.tensor(blocks[index], dtype=torch.long)
            return {"input_ids": values, "attention_mask": torch.ones_like(values), "labels": values.clone()}

    config = GPT2Config(
        vocab_size=len(tokenizer),
        n_positions=args.block_size,
        n_ctx=args.block_size,
        n_embd=args.hidden_size,
        n_layer=args.layers,
        n_head=args.heads,
        bos_token_id=tokenizer.bos_token_id,
        eos_token_id=tokenizer.eos_token_id,
        pad_token_id=tokenizer.pad_token_id,
    )
    model = GPT2LMHeadModel(config)
    model.config._name_or_path = args.repo_id
    model.generation_config.pad_token_id = tokenizer.pad_token_id
    model.generation_config.eos_token_id = tokenizer.eos_token_id

    train_args = TrainingArguments(
        output_dir=str(out / "training-checkpoints"),
        max_steps=args.steps,
        per_device_train_batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        weight_decay=0.01,
        warmup_steps=min(50, max(0, args.steps // 10)),
        logging_steps=max(1, min(25, args.steps // 20)),
        save_strategy="no",
        report_to=[],
        seed=args.seed,
        data_seed=args.seed,
        fp16=bool(torch.cuda.is_available()),
        use_cpu=not torch.cuda.is_available(),
    )
    trainer = Trainer(model=model, args=train_args, train_dataset=PackedDataset())
    print(f"Training fresh GPT-2-style model on {len(blocks)} corpus blocks.", flush=True)
    trainer.train()

    # Save actual model tensors as model.safetensors plus HF config/tokenizer files.
    model.save_pretrained(out, safe_serialization=True)
    tokenizer.save_pretrained(out)
    config.save_pretrained(out)
    parameter_count = sum(p.numel() for p in model.parameters())
    provenance = os.getenv("TRAINING_DATA_PROVENANCE", "Uploader-supplied corpus; exact sources and rights must be documented before redistribution.")
    card = f"""---
license: {args.license}
language:
- en
library_name: transformers
pipeline_tag: text-generation
tags:
- aries
- causal-lm
- trained-from-scratch
---

# {args.model_name}

## Summary

An experimental, small GPT-2-style causal language model trained from randomly initialized weights on a user-supplied text corpus. This is not the ARIES hosted API proxy and is not a conversion of the existing character n-gram baseline.

## Model details

- Architecture: GPT-2 causal language model (GPT2LMHeadModel)
- Parameters: {parameter_count:,}
- Layers / hidden size / attention heads: {args.layers} / {args.hidden_size} / {args.heads}
- Context length: {args.block_size} tokens
- Tokenizer vocabulary: {len(tokenizer)}
- Training steps: {args.steps}
- Random seed: {args.seed}
- Corpus file name: {corpus.name} (the corpus itself is not uploaded by this script)
- Declared corpus provenance: {provenance}

## Intended use and limitations

This is an experimental baseline. No claim is made that it matches modern foundation models, is leaderboard-eligible, or has strong general-purpose performance. Evaluate independently before use. Small or narrow training corpora can cause memorization, poor coverage, and inaccurate outputs.

## Training data and rights

Declared provenance: {provenance}\n\nThe uploader is responsible for checking the dataset card, license, attribution, and whether the corpus and resulting model may lawfully be used and redistributed. Do not publish an inaccurate license claim.

## Evaluation

No independent benchmark score is claimed. Run reproducible evaluation on a pinned revision before reporting performance.
"""
    (out / "README.md").write_text(card, encoding="utf-8")
    (out / ".gitignore").write_text("training-checkpoints/\n", encoding="utf-8")

    print(f"Exported files to: {out.resolve()}", flush=True)
    print(f"Parameter count: {parameter_count:,}", flush=True)

    # Validate the saved artifact from disk before any upload.
    from transformers import AutoModelForCausalLM, AutoTokenizer
    check_tokenizer = AutoTokenizer.from_pretrained(out, local_files_only=True)
    check_model = AutoModelForCausalLM.from_pretrained(out, local_files_only=True)
    check_inputs = check_tokenizer("ARIES model validation", return_tensors="pt")
    check_output = check_model.generate(
        **check_inputs,
        max_new_tokens=4,
        do_sample=False,
        pad_token_id=check_tokenizer.pad_token_id,
    )
    if check_output.shape[1] <= check_inputs["input_ids"].shape[1]:
        raise RuntimeError("Saved model reloaded but failed to generate tokens.")
    print("PASS: saved model and tokenizer reloaded; generation succeeded.", flush=True)

    if args.skip_upload:
        print("Upload skipped by --skip-upload.", flush=True)
        return 0

    api = HfApi(token=token)
    api.create_repo(repo_id=args.repo_id, repo_type="model", private=args.private, exist_ok=True)
    api.upload_folder(
        repo_id=args.repo_id,
        repo_type="model",
        folder_path=str(out),
        commit_message="Upload initial trained ARIES experimental causal LM",
        ignore_patterns=["training-checkpoints/**"],
    )
    visibility = "private" if args.private else "public"
    print(f"UPLOAD SUCCESS: https://huggingface.co/{args.repo_id} ({visibility} repository)", flush=True)
    print("This is a model upload, not leaderboard submission or certification.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
