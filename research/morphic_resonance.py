"""Exploratory, preregistered analysis helpers for morphic-resonance-style studies.

This module does not assume morphic resonance is real. It analyzes a simple
forced-choice experiment against a prespecified chance baseline. It is not a
substitute for a full protocol, independent replication, or expert statistical
review. Keep hypotheses, exclusions, stopping rules, and primary outcomes fixed
before collecting data.
"""
from __future__ import annotations

from math import comb
from typing import Any


def exact_binomial_test(
    successes: int,
    trials: int,
    chance_probability: float = 0.5,
) -> dict[str, Any]:
    """Return a two-sided exact binomial test against a prespecified chance rate.

    Args:
        successes: Number of correct/target outcomes.
        trials: Total number of valid trials, fixed by the protocol.
        chance_probability: Null probability for each independent trial.

    Notes:
        Assumes independent Bernoulli trials and a fixed stopping rule. If trials
        are clustered by participant/session, use an appropriate hierarchical or
        permutation analysis instead. A small p-value does not establish the
        proposed mechanism; biases and ordinary information leakage must first
        be excluded.
    """
    if isinstance(successes, bool) or isinstance(trials, bool):
        raise TypeError("successes and trials must be integers, not booleans")
    if not isinstance(successes, int) or not isinstance(trials, int):
        raise TypeError("successes and trials must be integers")
    if trials <= 0:
        raise ValueError("trials must be greater than zero")
    if not 0 <= successes <= trials:
        raise ValueError("successes must be between zero and trials")
    if not 0.0 < chance_probability < 1.0:
        raise ValueError("chance_probability must be strictly between 0 and 1")

    p = chance_probability
    probabilities = [
        comb(trials, k) * (p**k) * ((1.0 - p) ** (trials - k))
        for k in range(trials + 1)
    ]
    lower_tail = sum(probabilities[: successes + 1])
    upper_tail = sum(probabilities[successes:])
    p_value = min(1.0, 2.0 * min(lower_tail, upper_tail))

    return {
        "successes": successes,
        "trials": trials,
        "observed_rate": successes / trials,
        "chance_probability": p,
        "two_sided_exact_p_value": p_value,
        "interpretation": (
            "Result is statistically unusual under the stated null model; "
            "replication and bias controls are still required."
            if p_value < 0.05
            else "This test did not reject the stated chance baseline."
        ),
        "claim_limit": (
            "This result alone cannot establish morphic resonance or any "
            "nonlocal information-transfer mechanism."
        ),
    }
