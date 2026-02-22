from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Mapping, Iterable
import copy


Number = float 


@dataclass(slots=True)
class CountryState:
    """
    Stores the resource inventory for a single country at a single point in time.
    Missing resources are treated as 0.
    """
    name: str
    resources: Dict[str, Number] = field(default_factory=dict)

    def get(self, resource: str) -> Number:
        """Return amount of resource (defaults to 0)."""
        return float(self.resources.get(resource, 0.0))

    def has(self, reqs: Mapping[str, Number]) -> bool:
        """
        True if this country has at least the required amount of every resource in reqs.
        """
        for r, amt in reqs.items():
            if self.get(r) < float(amt):
                return False
        return True

    def add(self, resource: str, delta: Number) -> None:
        """
        Add delta to a resource. Delta may be negative.
        Raises ValueError if the result would go negative.
        """
        cur = self.get(resource)
        nxt = cur + float(delta)
        if nxt < 0:
            raise ValueError(
                f"{self.name}: insufficient {resource}. "
                f"current={cur}, delta={delta}, would_be={nxt}"
            )
        # Store 0s sparsely if you want (optional). Here we keep it simple:
        self.resources[resource] = nxt

    def apply_delta_map(self, deltas: Mapping[str, Number]) -> None:
        """
        Apply multiple resource deltas as one atomic update.
        If any would go negative, raise and do not partially apply.
        """
        # First check all
        for r, d in deltas.items():
            if self.get(r) + float(d) < 0:
                raise ValueError(
                    f"{self.name}: insufficient {r} for delta {d}. current={self.get(r)}"
                )
        # Then apply
        for r, d in deltas.items():
            self.add(r, d)


@dataclass(slots=True)
class WorldState:
    """
    Stores the state of the world at a single time: multiple countries with inventories.
    """
    countries: Dict[str, CountryState] = field(default_factory=dict)

    def get_country(self, name: str) -> CountryState:
        if name not in self.countries:
            raise KeyError(f"Unknown country: {name}")
        return self.countries[name]

    def copy(self) -> WorldState:
        """Deep copy so schedules can be simulated without mutating the original."""
        return copy.deepcopy(self)

    def country_names(self) -> Iterable[str]:
        return self.countries.keys()


@dataclass(slots=True)
class ResourceWeights:
    """
    Global resource weights (shared across countries in Parts 1 & 2).
    """
    weights: Dict[str, Number] = field(default_factory=dict)

    def get(self, resource: str) -> Number:
        return float(self.weights.get(resource, 0.0))