import pytest

from source.world_state import WorldState, CountryState, ResourceWeights


def test_country_get_defaults_to_zero():
    c = CountryState("X", {"Population": 10})
    assert c.get("Population") == 10.0
    assert c.get("Nonexistent") == 0.0


def test_country_has_requirements():
    c = CountryState("X", {"Timber": 5, "MetallicElements": 2})
    assert c.has({"Timber": 5})
    assert c.has({"Timber": 4, "MetallicElements": 2})
    assert not c.has({"Timber": 6})
    assert not c.has({"Electronics": 1})  # missing treated as 0


def test_country_add_and_no_negative():
    c = CountryState("X", {"Timber": 5})
    c.add("Timber", -2)
    assert c.get("Timber") == 3.0

    with pytest.raises(ValueError):
        c.add("Timber", -10)  # would go negative


def test_apply_delta_map_atomic():
    c = CountryState("X", {"A": 5, "B": 1})

    # This should fail and not partially apply anything
    with pytest.raises(ValueError):
        c.apply_delta_map({"A": -3, "B": -5})

    assert c.get("A") == 5.0
    assert c.get("B") == 1.0

    # This should succeed
    c.apply_delta_map({"A": -3, "B": +2, "C": 4})
    assert c.get("A") == 2.0
    assert c.get("B") == 3.0
    assert c.get("C") == 4.0


def test_world_get_country_and_copy_deep():
    w = WorldState({
        "Atlantis": CountryState("Atlantis", {"Timber": 10}),
        "Carpania": CountryState("Carpania", {"Timber": 0}),
    })

    assert w.get_country("Atlantis").get("Timber") == 10.0
    with pytest.raises(KeyError):
        w.get_country("Unknown")

    w2 = w.copy()
    w2.get_country("Atlantis").add("Timber", -5)

    # Original unchanged (deep copy)
    assert w.get_country("Atlantis").get("Timber") == 10.0
    assert w2.get_country("Atlantis").get("Timber") == 5.0


def test_resource_weights_default_zero():
    rw = ResourceWeights({"Housing": 2.0})
    assert rw.get("Housing") == 2.0
    assert rw.get("Missing") == 0.0