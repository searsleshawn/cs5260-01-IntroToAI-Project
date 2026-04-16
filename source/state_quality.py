# from __future__ import annotations

# from typing import Iterable, Optional

# from source.world_state import WorldState, ResourceWeights


# def state_quality(
#     world: WorldState,
#     country_name: str,
#     weights: ResourceWeights,
#     *,
#     exclude: Optional[Iterable[str]] = None,
#     pop_floor: float = 1.0,
# ) -> float:
#     """
#     Per-capita State Quality:

#         Q = sum_r w[r] * (amount[r] / max(Population, pop_floor))

#     - Uses all resources present in the country's inventory.
#     - Missing weights default to 0 via ResourceWeights.get().
#     - 'exclude' omits resources from scoring.
#     """
#     c = world.get_country(country_name)

#     population = c.get("Population")
#     denom = max(population, pop_floor)  # avoid division by zero

#     exclude_set = set(exclude) if exclude is not None else set()

#     total = 0.0
#     for r, amt in c.resources.items():
#         if r in exclude_set:
#             continue
#         w = weights.get(r)
#         total += w * (float(amt) / denom)

#     return float(total)


from __future__ import annotations

from typing import Iterable, Optional

from source.world_state import WorldState, ResourceWeights


def state_quality(
    world: WorldState,
    country_name: str,
    weights: ResourceWeights,
    *,
    pop_floor: float = 1.0,
) -> float:
    """
    Improved per-capita State Quality with saturation.

    Main ideas:
    - Normalize by population
    - Reward key resources only up to a target level
    - Keep waste as a penalty
    - Still allow raw materials to matter, but less strongly
    """
    c = world.get_country(country_name)

    population = max(c.get("Population"), pop_floor)

    def per_capita(resource: str) -> float:
        return c.get(resource) / population

    def capped_score(resource: str, target_per_capita: float) -> float:
        if target_per_capita <= 0:
            raise ValueError("target_per_capita must be positive")
        return min(per_capita(resource) / target_per_capita, 1.0)

    total = 0.0

    # --- Raw materials: helpful, but should not dominate forever ---
    total += weights.get("MetallicElements") * capped_score("MetallicElements", 0.5)
    total += weights.get("Timber") * capped_score("Timber", 0.5)

    # --- Intermediate goods: useful, but capped ---
    total += weights.get("MetallicAlloys") * capped_score("MetallicAlloys", 0.3)

    # --- Final goods: stronger importance, capped at realistic need ---
    total += weights.get("Housing") * capped_score("Housing", 1.0)
    total += weights.get("Electronics") * capped_score("Electronics", 0.5)

    # --- Waste remains harmful ---
    total += weights.get("MetallicAlloysWaste") * per_capita("MetallicAlloysWaste")
    total += weights.get("HousingWaste") * per_capita("HousingWaste")
    total += weights.get("ElectronicsWaste") * per_capita("ElectronicsWaste")

    return float(total)