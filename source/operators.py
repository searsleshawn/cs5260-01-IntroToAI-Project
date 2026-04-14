from __future__ import annotations
# from dataclasses import dataclass
from typing import Dict
from source.world_state import WorldState

# @dataclass
class Transform:
    def __init__(self, name: str, inputs: Dict[str, float], outputs: Dict[str, float]):
        self.name = name
        self.inputs = inputs
        self.outputs = outputs

def apply_transform(world: WorldState, country: str, transform: Transform) -> WorldState:
    update = world.copy()
    c = update.get_country(country)

    if not transform.inputs or not transform.outputs:
        raise ValueError(f"Invalid transform: {transform.name}")
    if not c.has(transform.inputs):
        raise ValueError(f"{country} cannot apply {transform.name}")

    
    # subtract inputs
    for r, amt in transform.inputs.items():
        c.add(r, -amt)
    # add outputs
    for r, amt in transform.outputs.items():
        c.add(r, amt)

    return update

def apply_transfer(world: WorldState, src: str, dst: str, resource: str, amount: float) -> WorldState:
    if amount <= 0:
        raise ValueError("Transfer amount must be positive")
    if src == dst:
        raise ValueError("Cannot transfer to same country")
    
    update = world.copy()

    c1 = update.get_country(src)
    c2 = update.get_country(dst)

    if c1.get(resource) < amount:
        raise ValueError(f"{src} has insufficient {resource}")
    
    c1.add(resource, -amount)
    c2.add(resource, amount)

    return update

def growth(world: WorldState) -> WorldState:
    update = world.copy()

    for country in update.countries.values():
        pop = country.get("Population")

        metallic_gain = max(1.0, pop // 50)
        timber_gain = max(1.0, pop // 40)

        country.add("MetallicElements", metallic_gain)
        country.add("Timber", timber_gain)
    
    return update