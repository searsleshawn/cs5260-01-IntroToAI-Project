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

from source.world_state import WorldState, ResourceWeights


def state_quality(
    world: WorldState,
    country_name: str,
    weights: ResourceWeights,
    *,
    pop_floor: float = 1.0,
) -> float:
    """
    State Quality model with:
    - strong penalty for unhoused population
    - electronics as a luxury / quality-of-life resource
    - weak direct value for intermediate goods
    - waste penalties
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

    housing = c.get("Housing")
    housed_ratio = min(housing / population, 1.0)
    unhoused_ratio = max(0.0, 1.0 - housed_ratio)

    # Strong nonlinear penalty for unhoused population.
    # Cubed penalty makes large housing shortages much more severe.
    total -= 12.0 * (unhoused_ratio ** 3)

    # Housing still gives direct positive welfare.
    total += 2.0 * weights.get("Housing") * housed_ratio

    # Electronics are a luxury / development good.
    total += 1.5 * weights.get("Electronics") * capped_score("Electronics", 0.2)

    # Very weak direct value for intermediate inventory.
    total += 0.05 * weights.get("MetallicAlloys") * capped_score("MetallicAlloys", 0.05)

    # Waste penalties.
    total += 1.2 * weights.get("MetallicAlloysWaste") * per_capita("MetallicAlloysWaste")
    total += 1.0 * weights.get("HousingWaste") * per_capita("HousingWaste")
    total += 1.2 * weights.get("ElectronicsWaste") * per_capita("ElectronicsWaste")

    # --- Production capacity penalty (weak, but important) ---
    total -= 0.2 * (1.0 - min(1.0, per_capita("MetallicElements") / 0.2))
    total -= 0.2 * (1.0 - min(1.0, per_capita("Timber") / 0.2))

    return float(total)