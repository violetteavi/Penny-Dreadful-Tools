import json
from pathlib import Path

import numpy as np
import pytest

from archetype_classifier.card_embeddings.combined import THIRDS, build_average_thirds, build_combined
from archetype_classifier.card_embeddings.combined_embedding import (
    FIT_COMBINER,
    LOAD_COMBINER,
    CombinedEmbedding,
    CombinedEmbeddingSettings,
    CombinedEmbeddingWeights,
    build_average_thirds_combiner,
    build_combined_embedding,
    build_season_label,
    build_season_set,
    combined_embedding_path,
    load_combined_embedding,
    save_combined_embedding,
)
from archetype_classifier.card_embeddings.combined_test import CARD_TEXT, NUMBERS
from archetype_classifier.card_embeddings.neighbours import Similarities
from archetype_classifier.card_embeddings.pool import Card, Face
from archetype_classifier.card_embeddings.text import MASKED
from archetype_classifier.card_embeddings.text_embedding_test import FakeEncoder


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
    assert build_average_thirds_combiner(NUMBERS, CombinedEmbeddingWeights(*weights)).group_shares() == pytest.approx(shares)


@pytest.mark.parametrize('weights', [(3, 1, 1, 1), (2, 1, 1, 0), (1, 0, 0, 0)])
def test_a_combiner_saved_as_json_and_loaded_back_gives_identical_similarities(weights: tuple[float, float, float, float]) -> None:
    combiner = FIT_COMBINER['average'](NUMBERS, CombinedEmbeddingWeights(*weights))
    saved = json.loads(json.dumps(combiner.to_json()))  # Through real JSON text, as the saved file will be.
    loaded = LOAD_COMBINER[saved['approach']](saved)
    assert loaded.weights == combiner.weights
    assert np.array_equal(similarities(loaded.combine(CARD_TEXT, NUMBERS)), similarities(combiner.combine(CARD_TEXT, NUMBERS)))


# Real cards with their real faces and the seasons they were legal in (decksite _legal_cards).
SHOCK = Card('Shock', 'normal', (Face('Shock', '{R}', 1, 'Instant', 'Shock deals 2 damage to any target.'),),
             build_season_set('1-3,5-7,9,13-33,35-43'))
KALONIAN_TUSKER = Card('Kalonian Tusker', 'normal', (Face('Kalonian Tusker', '{G}{G}', 2, 'Creature — Beast', '', '3', '3'),),
                       build_season_set('1,12-30,32-34,38-39,42'))
CITY_PIGEON = Card('City Pigeon', 'normal', (Face('City Pigeon', '{W}', 1, 'Creature — Bird', 'Flying\nWhen this creature leaves the battlefield, create a Food '
                                                  'token. (It\'s an artifact with "{2}, {T}, Sacrifice this token: You gain 3 life.")', '1', '1'),),
                   build_season_set('39-40'))
AJANIS_RESPONSE = Card("Ajani's Response", 'normal', (Face("Ajani's Response", '{4}{W}', 5, 'Instant', 'This spell costs {3} less to cast if it targets a '
                                                           'tapped creature.\nDestroy target creature.'),), build_season_set('42'))
POOL = [SHOCK, KALONIAN_TUSKER, CITY_PIGEON, AJANIS_RESPONSE]


def build(fit: str, embedded: str, weights: tuple[float, float, float, float] = (3, 1, 1, 1)) -> CombinedEmbedding:
    settings = CombinedEmbeddingSettings('fake', MASKED, build_season_set(fit), build_season_set(embedded))
    return build_combined_embedding(POOL, settings, 'average', CombinedEmbeddingWeights(*weights), FakeEncoder())


def test_the_embedding_holds_exactly_the_cards_legal_in_an_embedded_season() -> None:
    embedding = build('1-38', '1-39')
    assert embedding.names == ('City Pigeon', 'Kalonian Tusker', 'Shock')
    assert embedding.text.names == embedding.numbers.names == embedding.names


def test_the_statistics_are_fitted_on_the_fit_season_cards_only_but_applied_to_every_card() -> None:
    with_pigeon, without_pigeon = build('1-38', '1-39'), build('1-38', '1-38')
    assert 'City Pigeon' not in without_pigeon.names
    assert with_pigeon.combiner.to_json() == without_pigeon.combiner.to_json()
    pigeon = with_pigeon.names.index('City Pigeon')
    assert with_pigeon.similarities(pigeon, pigeon + 1)[0, pigeon] == pytest.approx(1)


def test_gapped_seasons_pick_cards_legal_in_any_of_them() -> None:
    embedding = build('2', '2,40')  # Shock was legal in 2 and 40, City Pigeon in 40; Kalonian Tusker in neither.
    assert embedding.names == ('City Pigeon', 'Shock')
    assert not np.isnan(embedding.similarities(0, 2)).any()


def test_an_encoder_other_than_the_one_the_settings_name_is_refused() -> None:
    settings = CombinedEmbeddingSettings('potion', MASKED, build_season_set('1-38'), build_season_set('1-39'))
    with pytest.raises(ValueError, match="settings name the encoder 'potion' but were given 'fake'"):
        build_combined_embedding(POOL, settings, 'average', CombinedEmbeddingWeights(3, 1, 1, 1), FakeEncoder())


def test_the_file_name_follows_the_settings_the_approach_and_the_weights() -> None:
    settings = CombinedEmbeddingSettings('potion', MASKED, build_season_set('1-38'), build_season_set('1-39'))
    path = combined_embedding_path(Path('embeddings'), settings, 'average', CombinedEmbeddingWeights(3, 1, 1, 1))
    assert path == Path('embeddings/potion__masked__average__w0.5-0.1667-0.1667-0.1667__fit1-38__emb1-39.npz')


@pytest.mark.parametrize('weights', [(3, 1, 1, 1), (1, 0, 0, 0)])
def test_a_saved_embedding_loads_back_with_the_same_settings_combiner_and_similarities(tmp_path: Path, weights: tuple[float, float, float, float]) -> None:
    embedding = build('1-38', '1-39', weights)
    path = save_combined_embedding(embedding, tmp_path)
    assert path == combined_embedding_path(tmp_path, embedding.settings, 'average', embedding.combiner.weights)
    assert sorted(p.name for p in tmp_path.iterdir()) == [path.with_suffix('.json').name, path.name]
    loaded = load_combined_embedding(path)
    assert loaded.settings == embedding.settings
    assert loaded.combiner.to_json() == embedding.combiner.to_json()
    assert loaded.names == embedding.names
    assert loaded.text.manifest == embedding.text.manifest
    assert np.array_equal(similarities(loaded), similarities(embedding))


def test_a_saved_file_whose_rows_dont_match_its_names_is_refused(tmp_path: Path) -> None:
    path = save_combined_embedding(build('1-38', '1-39'), tmp_path)
    saved = json.loads(path.with_suffix('.json').read_text())
    saved['names'] = saved['names'][:-1]
    path.with_suffix('.json').write_text(json.dumps(saved))
    with pytest.raises(ValueError, match=f'{path.name} has 3 rows but its .json lists 2 cards'):
        load_combined_embedding(path)
