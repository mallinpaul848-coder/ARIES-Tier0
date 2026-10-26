# PRISE Positive-Impact Math

## Purpose

The positive-impact scorer is a deterministic, explainable prioritization aid for
ARIES/MALLIN. It translates PRISE concepts—Priority, Risk, Impact, Systemic effect,
and Emergence—into a bounded score with explicit uncertainty and reversibility
penalties.

## Inputs

Every input is normalized to the closed interval [0, 1]:
- `priority`: urgency/importance.
- `benefit`: expected positive outcome.
- `risk`: expected harm or failure exposure (higher is worse).
- `systemic_effect`: estimated breadth of effects across connected systems.
- `emergence`: expected additional benefit from interactions.
- `confidence`: evidence strength for the estimates.
- `reversibility`: how readily the action can be rolled back.

## Formula

```text
upside = 0.35*benefit + 0.20*priority + 0.20*systemic_effect
       + 0.10*emergence + 0.15*confidence
risk_penalty = 0.60*risk + 0.25*(1-confidence) + 0.15*(1-reversibility)
score = clamp(upside * (1-risk_penalty), 0, 1)
```

Default bands are 0.70–1.00 high-priority review, 0.40–0.699999 consider,
and below 0.40 defer-or-revise. They are provisional policy choices, not learned
or independently validated thresholds. The score is a ranking heuristic, not a
truth probability, causal estimate, safety guarantee, or substitute for human review.

## Mallin math signals

Base-10 digital root and Phase-8 ring position are reported as experimental
descriptors for analysis and repeatability. They do **not** alter the core score
or imply that numerological patterns predict correctness. These signals should
only be promoted into scoring after preregistered, held-out experiments show
reproducible gains against simple baselines.

## Validation

Run:

```bash
python -m unittest tests.test_positive_impact -v
```

Recommended next research step: compare this scorer with benefit-only and random
ranking baselines on held-out, domain-reviewed decisions. Report ranking quality,
calibration, false-positive harm, subgroup effects, and confidence intervals.
Do not claim performance improvement until measured.
