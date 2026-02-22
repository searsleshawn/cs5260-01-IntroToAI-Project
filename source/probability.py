from __future__ import annotations

import math


def acceptance_probability(dr: float, *, k: float = 1.0, x0: float = 0.0) -> float:
    """
    P(c, s) = 1 / (1 + e^(-k*(dr - x0)))
    where dr is the discounted reward for that country on that schedule.
    """
    # Stable sigmoid
    z = k * (dr - x0)
    if z >= 0:
        ez = math.exp(-z)
        return 1.0 / (1.0 + ez)
    else:
        ez = math.exp(z)
        return ez / (1.0 + ez)


def schedule_success_probability(country_probs: list[float]) -> float:
    """
    P(s) = Π_i P(c_i, s)
    """
    p = 1.0
    for x in country_probs:
        if x < 0.0 or x > 1.0:
            raise ValueError(f"Invalid probability: {x}")
        p *= x
    return p