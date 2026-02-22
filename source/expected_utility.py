from __future__ import annotations

from source.world_state import WorldState, ResourceWeights
from source.score import discounted_reward
from source.probability import acceptance_probability, schedule_success_probability


def expected_utility(
    world_start: WorldState,
    world_end: WorldState,
    *,
    self_country: str,
    participant_countries: list[str],
    weights: ResourceWeights,
    gamma: float,
    N: int,
    k: float,
    x0: float,
    C: float,
) -> float:
    """
    EU(s) = P(s) * DR(self, s) + (1 - P(s)) * C

    where:
      - DR(self, s) = discounted_reward for the 'self_country'
      - P(s) = product over participants of sigmoid(DR(country, s))
      - sigmoid(DR) = 1 / (1 + exp(-k*(DR-x0)))
      - C = utility if schedule fails (penalty / fallback)
    """
    # 1) Compute discounted reward for each participant and convert to acceptance probability
    probs: list[float] = []
    for c in participant_countries:
        dr_c = discounted_reward(world_start, world_end, c, weights, gamma=gamma, N=N)
        probs.append(acceptance_probability(dr_c, k=k, x0=x0))

    # 2) Multiply into schedule success probability
    p_schedule = schedule_success_probability(probs)

    # 3) Compute self discounted reward
    dr_self = discounted_reward(world_start, world_end, self_country, weights, gamma=gamma, N=N)

    # 4) Expected Utility
    return (p_schedule * dr_self) + ((1.0 - p_schedule) * C)