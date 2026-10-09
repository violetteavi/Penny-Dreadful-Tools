"""Deck vectors on a small embedding of the scenario cards (Scenarios.md, "The nearest deck on the combined embedding")."""
from collections import Counter

import numpy as np

from archetype_classifier.card_embeddings.combined_embedding import CombinedEmbedding, CombinedEmbeddingSettings, CombinedEmbeddingWeights, build_combined_embedding, build_season_set
from archetype_classifier.card_embeddings.deck_vectors import build_deck_vectors
from archetype_classifier.card_embeddings.pool import Card, Face
from archetype_classifier.card_embeddings.text import MASKED
from archetype_classifier.card_embeddings.text_embedding_test import FakeEncoder
from archetype_classifier.data_loading.dataset import CardCount

# Real cards with their real faces, legal in seasons 30 and 39 (each is legal in more; the pool only needs these two).
SEASONS = build_season_set('30,39')
SCENARIO_POOL = [
    Card('Shock', 'normal', (Face('Shock', '{R}', 1, 'Instant', 'Shock deals 2 damage to any target.'),), SEASONS),
    Card('Burst Lightning', 'normal', (Face('Burst Lightning', '{R}', 1, 'Instant', 'Kicker {4} (You may pay an additional {4} as you cast this spell.)\n'
                                            'Burst Lightning deals 2 damage to any target. If this spell was kicked, it deals 4 damage instead.'),), SEASONS),
    Card('Mountain', 'normal', (Face('Mountain', '', 0, 'Basic Land — Mountain', '({T}: Add {R}.)'),), SEASONS),
    Card('Essence Scatter', 'normal', (Face('Essence Scatter', '{1}{U}', 2, 'Instant', 'Counter target creature spell.'),), SEASONS),
    Card('Negate', 'normal', (Face('Negate', '{1}{U}', 2, 'Instant', 'Counter target noncreature spell.'),), SEASONS),
    Card('Island', 'normal', (Face('Island', '', 0, 'Basic Land — Island', '({T}: Add {U}.)'),), SEASONS),
    # A vanilla creature, so the stats group has length: with no stats on any fitted card, every group scale comes out NaN (#49).
    Card('Kalonian Tusker', 'normal', (Face('Kalonian Tusker', '{G}{G}', 2, 'Creature — Beast', '', '3', '3'),), SEASONS),
]

def scenario_embedding() -> CombinedEmbedding:
    """The six scenario cards and Kalonian Tusker. Smaug's Fury, legal only in season 43, isn't in it."""
    settings = CombinedEmbeddingSettings('fake', MASKED, SEASONS, SEASONS)
    return build_combined_embedding(SCENARIO_POOL, settings, 'average', CombinedEmbeddingWeights(3, 1, 1, 1), FakeEncoder())

def cards(**counts: int) -> tuple[CardCount, ...]:
    """Card names written as keywords: underscores are spaces, and "_s_" is "'s " (Smaug_s_Fury is Smaug's Fury)."""
    return tuple(sorted((CardCount(name.replace('_s_', "'s ").replace('_', ' '), n) for name, n in counts.items()), key=lambda c: c.card))

def unit(v: np.ndarray) -> np.ndarray:
    return v / np.linalg.norm(v)

EMBEDDING = scenario_embedding()
ROW = {name: EMBEDDING.vectors[i].astype(np.float64) for i, name in enumerate(EMBEDDING.names)}


# Scenario: copies weigh the deck vector, basic lands count, and the sideboard doesn't (the sideboard is checked on the model).

def test_the_small_embedding_has_finite_scales_so_its_numbers_count() -> None:
    assert np.isfinite(EMBEDDING.combiner.statistics.scales).all()  # type: ignore[attr-defined]

def test_a_deck_vector_is_the_copy_weighted_average_at_unit_length() -> None:
    vectors = build_deck_vectors([cards(Shock=4, Mountain=56)], EMBEDDING)
    assert np.allclose(vectors.matrix[0], unit(4 * ROW['Shock'] + 56 * ROW['Mountain']))
    assert np.isclose(np.linalg.norm(vectors.matrix[0]), 1)
    assert (vectors.embedded.tolist(), vectors.skipped.tolist(), vectors.skipped_cards) == ([60], [0], Counter())

def test_doubling_every_count_gives_the_same_vector() -> None:
    vectors = build_deck_vectors([cards(Shock=4, Mountain=56), cards(Shock=8, Mountain=112)], EMBEDDING)
    assert np.allclose(vectors.matrix[0], vectors.matrix[1])

def test_basic_lands_count() -> None:
    vectors = build_deck_vectors([cards(Shock=4, Mountain=56), cards(Shock=4, Island=56), cards(Mountain=60)], EMBEDDING)
    assert not np.allclose(vectors.matrix[0], vectors.matrix[1])
    assert np.allclose(vectors.matrix[2], unit(ROW['Mountain']))


# Scenario: a card missing from the embedding is skipped and counted.

def test_a_missing_card_is_skipped_and_counted() -> None:
    vectors = build_deck_vectors([cards(Shock=4, Mountain=52, Smaug_s_Fury=4), cards(Shock=4, Mountain=52)], EMBEDDING)
    assert np.allclose(vectors.matrix[0], vectors.matrix[1])
    assert (vectors.embedded.tolist(), vectors.skipped.tolist()) == ([56, 56], [4, 0])
    assert vectors.skipped_cards == Counter({"Smaug's Fury": 4})

def test_a_deck_of_only_missing_cards_has_a_zero_vector() -> None:
    vectors = build_deck_vectors([cards(Smaug_s_Fury=60)], EMBEDDING)
    assert not vectors.matrix[0].any()
    assert (vectors.embedded.tolist(), vectors.skipped.tolist()) == ([0], [60])

def test_no_decks_give_an_empty_matrix() -> None:
    vectors = build_deck_vectors([], EMBEDDING)
    assert vectors.matrix.shape == (0, EMBEDDING.vectors.shape[1])
