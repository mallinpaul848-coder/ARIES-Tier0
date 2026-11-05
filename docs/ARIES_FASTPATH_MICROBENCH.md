# ARIES fast-path microbenchmark

A component benchmark should compare the direct deterministic solver, the cache-disabled FastPathEngine, and the warm-cache FastPathEngine. It should also verify exact outputs and measure concurrent throughput.

Run on the same host and Python build for before/after comparisons. Preserve raw JSON, commit SHA, host details, and at least five independent repetitions; compare medians across runs.

This measures only in-process routing/cache behavior. It excludes HTTP, JSON serialization, socket scheduling, model inference, and power draw. Warm-cache results apply only to repeated identical prompts. Do not present component timings as full-gateway latency, exchange/HFT qualification, or electricity savings.
