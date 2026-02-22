from source.world_state import WorldState, CountryState, ResourceWeights
from source.score import undiscounted_reward, discounted_reward


def test_reward():
    weights = ResourceWeights({"MetallicElements": 1.0})

    w0 = WorldState({
        "A": CountryState("A", {"Population": 100, "MetallicElements": 0})
    })

    w1 = WorldState({
        "A": CountryState("A", {"Population": 100, "MetallicElements": 100})
    })

    r = undiscounted_reward(w0, w1, "A", weights)
    assert r == 1.0  # 100/100

    dr = discounted_reward(w0, w1, "A", weights, gamma=0.9, N=1)
    assert abs(dr - 0.9) < 1e-9