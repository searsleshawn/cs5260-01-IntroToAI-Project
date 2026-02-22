import pytest

from source.world_state import WorldState, CountryState, ResourceWeights
from source.expected_utility import expected_utility


def test_expected_utility_bounds_deterministic_case():
    # Weights: Food positive, Pollution negative (Population 0 to avoid constant term)
    weights = ResourceWeights({
        "Population": 0.0,
        "Food": 1.0,
        "Pollution": -1.0,
    })

    # Start state
    w0 = WorldState({
        "A": CountryState("A", {"Population": 100, "Food": 0, "Pollution": 0}),
        "B": CountryState("B", {"Population": 100, "Food": 0, "Pollution": 0}),
    })

    # End state (ΔQ per-capita = 0.4)
    w1 = WorldState({
        "A": CountryState("A", {"Population": 100, "Food": 50, "Pollution": 10}),
        "B": CountryState("B", {"Population": 100, "Food": 50, "Pollution": 10}),
    })

    eu = expected_utility(
        w0, w1,
        self_country="A",
        participant_countries=["A", "B"],
        weights=weights,
        gamma=0.9,
        N=2,
        k=1.0,
        x0=0.0,
        C=-1.0,
    )

    # Assert bounds
    assert eu > -0.669
    assert eu < 0.324


def test_expected_utility_participants_product_effect():
    weights = ResourceWeights({
        "Population": 0.0,
        "Housing": 1.0,
        "HousingWaste": -1.0,
    })

    w0 = WorldState({
        "A": CountryState("A", {"Population": 100, "Housing": 0, "HousingWaste": 0}),
        "B": CountryState("B", {"Population": 100, "Housing": 0, "HousingWaste": 0}),
        "C": CountryState("C", {"Population": 100, "Housing": 0, "HousingWaste": 0}),
    })

    w1 = WorldState({
        "A": CountryState("A", {"Population": 100, "Housing": 10, "HousingWaste": 0}),
        "B": CountryState("B", {"Population": 100, "Housing": 10, "HousingWaste": 0}),
        "C": CountryState("C", {"Population": 100, "Housing": 10, "HousingWaste": 0}),
    })

    # EU with 2 participants vs 3 participants should be lower (product of probs)
    eu_2 = expected_utility(
        w0, w1,
        self_country="A",
        participant_countries=["A", "B"],
        weights=weights,
        gamma=0.9,
        N=1,
        k=1.0,
        x0=0.0,
        C=-1.0,
    )

    eu_3 = expected_utility(
        w0, w1,
        self_country="A",
        participant_countries=["A", "B", "C"],
        weights=weights,
        gamma=0.9,
        N=1,
        k=1.0,
        x0=0.0,
        C=-1.0,
    )

    assert eu_3 < eu_2