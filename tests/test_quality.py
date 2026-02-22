from source.world_state import WorldState, CountryState, ResourceWeights
from source.quality import state_quality


def test_state_quality_basic():
    world = WorldState({
        "A": CountryState("A", {
            "Population": 100,
            "MetallicElements": 50,
            "MetallicAlloysWaste": 10
        })
    })

    weights = ResourceWeights({
        "MetallicElements": 1.0,
        "MetallicAlloysWaste": -1.0,
    })

    q = state_quality(world, "A", weights)

    # (50/100) - (10/100) = 0.5 - 0.1 = 0.4
    assert abs(q - 0.4) < 1e-9