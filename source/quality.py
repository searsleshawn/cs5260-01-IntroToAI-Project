from __future__ import annotations

from typing import Iterable, Optional

from source.world_state import WorldState, ResourceWeights


def state_quality(
    world: WorldState,
    country_name: str,
    weights: ResourceWeights,
    *,
    exclude: Optional[Iterable[str]] = None,
    pop_floor: float = 1.0,
) -> float:
    """
    Per-capita State Quality:

        Q = sum_r w[r] * (amount[r] / max(Population, pop_floor))

    - Uses all resources present in the country's inventory.
    - Missing weights default to 0 via ResourceWeights.get().
    - 'exclude' lets you omit resources from scoring if you want (optional).
    """
    c = world.get_country(country_name)

    population = c.get("Population")
    denom = max(population, pop_floor)  # avoid division by zero

    exclude_set = set(exclude) if exclude is not None else set()

    total = 0.0
    for r, amt in c.resources.items():
        if r in exclude_set:
            continue
        w = weights.get(r)
        total += w * (float(amt) / denom)

    return float(total)