from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from source.world_state import WorldState, ResourceWeights
from source.quality import state_quality


@dataclass(frozen=True, slots=True)
class ScoreParams:
    gamma: float = 0.9  # discount factor in [0, 1)
    x0: float = 0.0     # reserved for later (logistic), not used here
    k: float = 1.0      # reserved for later (logistic), not used here
    C: float = -1.0     # reserved for later (EU failure cost), not used here


def undiscounted_reward(
    world_start: WorldState,
    world_end: WorldState,
    country_name: str,
    weights: ResourceWeights,
) -> float:
    """
    R(c, s) = Q_end(c) - Q_start(c)
    """
    q_start = state_quality(world_start, country_name, weights)
    q_end = state_quality(world_end, country_name, weights)
    return q_end - q_start


def discounted_reward(
    world_start: WorldState,
    world_end: WorldState,
    country_name: str,
    weights: ResourceWeights,
    *,
    gamma: float,
    N: int,
) -> float:
    """
    DR(c, s) = gamma^N * (Q_end - Q_start)
    """
    if not (0.0 <= gamma < 1.0):
        raise ValueError("gamma must be in [0, 1).")
    if N < 0:
        raise ValueError("N must be >= 0.")

    r = undiscounted_reward(world_start, world_end, country_name, weights)
    return (gamma ** N) * r