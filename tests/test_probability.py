from source.probability import acceptance_probability, schedule_success_probability


def test_sigmoid_zero():
    assert abs(acceptance_probability(0.0) - 0.5) < 1e-12


def test_schedule_product():
    assert schedule_success_probability([0.5, 0.5]) == 0.25