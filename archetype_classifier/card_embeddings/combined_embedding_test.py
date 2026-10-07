import pytest

from archetype_classifier.card_embeddings.combined_embedding import CombinedEmbeddingWeights, build_season_label, build_season_set


def values(weights: CombinedEmbeddingWeights) -> tuple[float, float, float, float]:
    return weights.text, weights.mana_value, weights.colour, weights.stats


def test_weights_keep_only_their_ratios_normalised_over_all_four() -> None:
    assert values(CombinedEmbeddingWeights(3, 1, 1, 1)) == pytest.approx((1 / 2, 1 / 6, 1 / 6, 1 / 6))
    assert values(CombinedEmbeddingWeights(1 / 2, 1 / 6, 1 / 6, 1 / 6)) == pytest.approx(values(CombinedEmbeddingWeights(3, 1, 1, 1)))


@pytest.mark.parametrize(('weights', 'problem'), [
    ((1, -1, 0, 0), 'negative'),
    ((1, float('nan'), 1, 1), 'finite'),
    ((1, float('inf'), 1, 1), 'finite'),
    ((0, 0, 0, 0), 'all four'),
])
def test_negative_non_finite_and_all_zero_weights_are_refused(weights: tuple[float, float, float, float], problem: str) -> None:
    with pytest.raises(ValueError, match=problem):
        CombinedEmbeddingWeights(*weights)


def test_zeros_are_allowed_so_text_alone_and_numbers_alone_are_valid_weights() -> None:
    assert values(CombinedEmbeddingWeights(1, 0, 0, 0)) == (1, 0, 0, 0)
    assert values(CombinedEmbeddingWeights(0, 1, 1, 1)) == pytest.approx((0, 1 / 3, 1 / 3, 1 / 3))


def test_a_season_set_is_written_as_ranges_and_single_seasons() -> None:
    assert build_season_set('1-3,6-8,10,12,14') == frozenset({1, 2, 3, 6, 7, 8, 10, 12, 14})
    assert build_season_set('1-38') == frozenset(range(1, 39))


@pytest.mark.parametrize(('seasons', 'label'), [
    ({1, 2, 3, 6, 7, 8, 10, 12, 14}, '1-3_6-8_10_12_14'),
    (set(range(1, 40)), '1-39'),
    ({39}, '39'),
    ({6, 7}, '6-7'),
])
def test_a_season_set_is_labelled_for_file_names_as_ranges(seasons: set[int], label: str) -> None:
    assert build_season_label(frozenset(seasons)) == label
