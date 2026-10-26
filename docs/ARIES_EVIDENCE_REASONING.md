# ARIES Evidence-Aware Reasoning Scaffold

## What this adds

This module adds an explicit, deterministic scaffold for question decomposition,
hypothesis comparison, evidence tracking, basic contradiction flags, and next-step
recommendations. It is designed to support ARIES reasoning workflows and to be
composable with the PRISE positive-impact scorer.

## Reasoning flow

1. Normalize and classify the question's goal.
2. Represent candidate explanations as named hypotheses.
3. Attach evidence with an explicit support target, source label, and strength.
4. Rank candidates using a transparent heuristic; do not call the scores probabilities.
5. Flag simple explicit-negation pairs.
6. Recommend disconfirming evidence or conflict resolution.

## Limits

The code does not itself verify sources, understand arbitrary natural language,
or improve the underlying model weights. The conflict detector is deliberately
narrow. Use a capable language model or domain-specific parser to propose candidates,
then use this module to structure and audit the evidence. For health and psychology,
avoid inferring diagnoses, intent, or personality from writing alone; high-stakes
outputs require appropriate professional review.

## Tests

Run:
```bash
python -m unittest discover -s tests -p "test_reasoning_engine.py" -v
```

## Evaluation before claiming improvement

Compare against the current ARIES baseline on held-out tasks. Measure answer accuracy,
evidence attribution, contradiction recall/precision, calibration, abstention quality,
latency, and regression rate. Include adversarial and high-stakes examples. Do not
claim reasoning or intelligence gains unless independent, reproducible results show them.
