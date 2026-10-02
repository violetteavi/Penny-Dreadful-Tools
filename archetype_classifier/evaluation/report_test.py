from archetype_classifier.evaluation.report import number


def test_a_value_that_rounds_to_zero_never_shows_as_negative_zero() -> None:
    assert [number(v) for v in (-0.0004, -0.0, 0.0, 0.004, -0.006, None, float('nan'))] == ['0.00', '0.00', '0.00', '0.00', '-0.01', '—', '—']
