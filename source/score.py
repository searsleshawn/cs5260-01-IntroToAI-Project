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


"""
Simple score test
"""
if __name__ == "__main__":
    from world_state import CountryState, WorldState, ResourceWeights

    weights = ResourceWeights({
        "Population": 0.0,
        "Food": 1.0,
        "Pollution": -1.0,
    })

    # Start world
    w0 = WorldState({
        "A": CountryState("A", {"Population": 100, "Food": 0, "Pollution": 0})
    })

    # End world: A gained food, gained some pollution
    w1 = WorldState({
        "A": CountryState("A", {"Population": 100, "Food": 50, "Pollution": 10})
    })

    # Per-capita Q0 = 1*(0/100) + (-1)*(0/100) = 0
    # Per-capita Q1 = 1*(50/100) + (-1)*(10/100) = 0.5 - 0.1 = 0.4
    # R = 0.4
    r = undiscounted_reward(w0, w1, "A", weights)
    assert abs(r - 0.4) < 1e-9, r

    dr = discounted_reward(w0, w1, "A", weights, gamma=0.9, N=2)
    # DR = 0.9^2 * 0.4 = 0.81 * 0.4 = 0.324
    assert abs(dr - 0.324) < 1e-9, dr

    print("Score tests passed.")