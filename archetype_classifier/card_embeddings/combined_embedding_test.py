import numpy as np
import pytest

from archetype_classifier.card_embeddings.combined import THIRDS, build_average_thirds, build_combined
from archetype_classifier.card_embeddings.combined_embedding import FIT_COMBINER, CombinedEmbeddingSettings, CombinedEmbeddingWeights, build_season_label, build_season_set, fit_average_thirds
from archetype_classifier.card_embeddings.combined_test import CARD_TEXT, NUMBERS
from archetype_classifier.card_embeddings.neighbours import Similarities
from archetype_classifier.card_embeddings.text import MASKED


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


@pytest.mark.parametrize('text', ['', '3-1', '1-', 'a', '1,,2', '0-3', '1-3-5'])
def test_malformed_season_text_is_refused_naming_the_text(text: str) -> None:
    with pytest.raises(ValueError, match='Seasons must be written like 1-38 or 1-3,6,8'):
        build_season_set(text)


def test_settings_with_gapped_seasons_inside_the_embedded_seasons_are_accepted() -> None:
    settings = CombinedEmbeddingSettings('potion', MASKED, build_season_set('1-3,6-8,10'), build_season_set('1-12'))
    assert settings.fit_seasons == frozenset({1, 2, 3, 6, 7, 8, 10})


@pytest.mark.parametrize(('fit', 'embedded', 'problem'), [
    ('', '1-39', 'at least one fit season'),
    ('1-38', '2-39', 'fit seasons 1 are not embedded'),
    ('1-40', '1-39', 'fit seasons 40 are not embedded'),
])
def test_settings_refuse_no_fit_seasons_or_fit_seasons_that_are_not_embedded(fit: str, embedded: str, problem: str) -> None:
    with pytest.raises(ValueError, match=problem):
        CombinedEmbeddingSettings('potion', MASKED, build_season_set(fit) if fit else frozenset(), build_season_set(embedded))


def similarities(cards: Similarities) -> np.ndarray:
    return np.asarray(cards.similarities(0, len(cards.names)))


def test_average_thirds_at_3_1_1_1_is_the_7_combination_at_alpha_one_half() -> None:
    combiner = FIT_COMBINER['average'](NUMBERS, CombinedEmbeddingWeights(3, 1, 1, 1))
    seven = build_combined(CARD_TEXT, build_average_thirds(NUMBERS, THIRDS).apply(NUMBERS), 0.5)
    assert np.allclose(similarities(combiner.combine(CARD_TEXT, NUMBERS)), similarities(seven), atol=1e-6)


def combined(*weights: float) -> np.ndarray:
    return similarities(FIT_COMBINER['average'](NUMBERS, CombinedEmbeddingWeights(*weights)).combine(CARD_TEXT, NUMBERS))


def test_a_zero_group_weight_is_the_limit_of_a_tiny_one() -> None:
    assert np.allclose(combined(2, 1, 1, 0), combined(2, 1, 1, 1e-6), atol=1e-4)
    assert np.allclose(combined(2, 0, 1, 1), combined(2, 1e-6, 1, 1), atol=1e-4)


def test_text_alone_is_exactly_the_text_cosine_and_nothing_is_ever_nan() -> None:
    assert np.allclose(combined(1, 0, 0, 0), similarities(CARD_TEXT), atol=1e-6)
    for weights in [(1, 0, 0, 0), (0, 1, 1, 1), (2, 1, 1, 0), (0, 1, 0, 0), (3, 1, 1, 1)]:
        assert not np.isnan(combined(*weights)).any(), weights


@pytest.mark.parametrize(('weights', 'shares'), [
    ((3, 1, 1, 1), (1 / 3, 1 / 3, 1 / 3)),
    ((2, 1, 1, 0), (1 / 2, 1 / 2, 0)),
    ((1, 0, 0, 0), (0, 0, 0)),
])
def test_group_shares_are_each_groups_part_of_the_numbers_weight(weights: tuple[float, float, float, float], shares: tuple[float, float, float]) -> None:
    assert fit_average_thirds(NUMBERS, CombinedEmbeddingWeights(*weights)).group_shares() == pytest.approx(shares)
