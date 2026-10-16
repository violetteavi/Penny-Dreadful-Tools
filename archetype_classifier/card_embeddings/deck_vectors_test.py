"""Deck vectors on a small embedding of the scenario cards (Scenarios.md, "The nearest deck on the combined embedding")."""
import math
from collections import Counter

import numpy as np
from scipy import sparse

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


# Scenario: card weights and √copies shape the deck vector (b) (#50). Weights from the scenario's training decks.

WEIGHTS = {'Shock': 1.8109, 'Mountain': 1.5878, 'Island': 1.5878, 'Essence Scatter': 1.8109, 'Divination': 3.1972}

def test_card_weights_and_square_root_copies_weigh_each_line() -> None:
    vectors = build_deck_vectors([cards(Shock=4, Mountain=56)], EMBEDDING, WEIGHTS.__getitem__, math.sqrt)
    assert np.allclose(vectors.matrix[0], unit(2 * 1.8109 * ROW['Shock'] + math.sqrt(56) * 1.5878 * ROW['Mountain']))
    assert (vectors.embedded.tolist(), vectors.skipped.tolist()) == ([60], [0])  # Counts stay in copies.

def test_card_weights_with_linear_copies() -> None:
    vectors = build_deck_vectors([cards(Shock=4, Mountain=56)], EMBEDDING, WEIGHTS.__getitem__)
    assert np.allclose(vectors.matrix[0], unit(4 * 1.8109 * ROW['Shock'] + 56 * 1.5878 * ROW['Mountain']))

def test_square_root_copies_shift_the_balance_but_not_under_doubling() -> None:
    vectors = build_deck_vectors([cards(Shock=4, Mountain=56), cards(Shock=8, Mountain=112)], EMBEDDING, copies=math.sqrt)
    assert np.allclose(vectors.matrix[0], vectors.matrix[1])  # Every line times the square root of 2.
    linear = build_deck_vectors([cards(Shock=4, Mountain=56)], EMBEDDING)
    shock = unit(ROW['Shock'])
    assert vectors.matrix[0] @ shock > linear.matrix[0] @ shock  # The four-of counts for more against 56 basics.

def test_no_weights_and_linear_copies_give_todays_vectors_exactly() -> None:
    decks = [cards(Shock=4, Mountain=56), cards(Essence_Scatter=4, Negate=4, Island=52), cards(Shock=4, Mountain=52, Smaug_s_Fury=4)]
    today = build_deck_vectors(decks, EMBEDDING)
    explicit = build_deck_vectors(decks, EMBEDDING, lambda card: 1.0, float)
    assert np.array_equal(today.matrix, explicit.matrix)
    assert (today.embedded.tolist(), today.skipped.tolist(), today.skipped_cards) == (explicit.embedded.tolist(), explicit.skipped.tolist(), explicit.skipped_cards)

def test_a_missing_card_is_still_skipped_and_counted_with_weights() -> None:
    vectors = build_deck_vectors([cards(Shock=4, Mountain=52, Smaug_s_Fury=4)], EMBEDDING, WEIGHTS.__getitem__, math.sqrt)
    assert np.allclose(vectors.matrix[0], unit(2 * 1.8109 * ROW['Shock'] + math.sqrt(52) * 1.5878 * ROW['Mountain']))
    assert (vectors.embedded.tolist(), vectors.skipped.tolist()) == ([56], [4])


# Scenario: in the embedding average, an unseen card counts through its rules text (b). The small embedding plus Divination, which no training deck plays.

def divination_embedding() -> CombinedEmbedding:
    pool = [*SCENARIO_POOL, Card('Divination', 'normal', (Face('Divination', '{2}{U}', 3, 'Sorcery', 'Draw two cards.'),), SEASONS)]
    return build_combined_embedding(pool, CombinedEmbeddingSettings('fake', MASKED, SEASONS, SEASONS), 'average', CombinedEmbeddingWeights(3, 1, 1, 1), FakeEncoder())

def test_an_unseen_card_the_embedding_knows_moves_the_deck_unevenly() -> None:
    embedding = divination_embedding()
    row = {name: embedding.vectors[i].astype(np.float64) for i, name in enumerate(embedding.names)}
    blue, red = cards(Essence_Scatter=4, Island=56), cards(Shock=4, Mountain=56)
    with_it, without_it = cards(Divination=4, Essence_Scatter=4, Island=52), cards(Essence_Scatter=4, Island=52)
    vectors = build_deck_vectors([with_it, without_it, blue, red], embedding, WEIGHTS.__getitem__, math.sqrt)
    assert np.allclose(vectors.matrix[0], unit(2 * 3.1972 * row['Divination'] + 2 * 1.8109 * row['Essence Scatter'] + math.sqrt(52) * 1.5878 * row['Island']))
    assert (vectors.embedded.tolist()[0], vectors.skipped.tolist()[0]) == (60, 0)  # An unseen card isn't a skipped card.
    blue_ratio, red_ratio = ((vectors.matrix[0] @ vectors.matrix[r]) / (vectors.matrix[1] @ vectors.matrix[r]) for r in (2, 3))
    assert not np.isclose(blue_ratio, red_ratio)  # Unlike in the bag, not one factor for every row.


# The lines behind each vector (#64): each line's copies(n) x weight, divided by the deck's unscaled length, so lines @ E gives the vector.

def test_lines_times_the_embedding_give_the_deck_vectors() -> None:
    decks = [cards(Shock=4, Mountain=56), cards(Essence_Scatter=4, Island=56), cards(Shock=4, Mountain=52, Smaug_s_Fury=4)]
    vectors = build_deck_vectors(decks, EMBEDDING, WEIGHTS.__getitem__, math.sqrt)
    assert np.allclose(vectors.lines @ EMBEDDING.vectors.astype(np.float64), vectors.matrix)

def test_each_line_is_its_copies_and_weight_over_the_decks_length() -> None:
    vectors = build_deck_vectors([cards(Shock=4, Mountain=56)], EMBEDDING, WEIGHTS.__getitem__, math.sqrt)
    length = np.linalg.norm(2 * 1.8109 * ROW['Shock'] + math.sqrt(56) * 1.5878 * ROW['Mountain'])
    column = {name: i for i, name in enumerate(EMBEDDING.names)}
    row = vectors.lines.toarray()[0]
    assert np.isclose(row[column['Shock']], 2 * 1.8109 / length)
    assert np.isclose(row[column['Mountain']], math.sqrt(56) * 1.5878 / length)
    assert np.count_nonzero(row) == 2
    assert vectors.lines.shape == (1, len(EMBEDDING.names))

def test_a_deck_of_only_missing_cards_has_no_lines() -> None:
    vectors = build_deck_vectors([cards(Smaug_s_Fury=60), cards(Shock=4, Mountain=56)], EMBEDDING)
    assert vectors.lines.getrow(0).nnz == 0
    assert vectors.lines.getrow(1).nnz == 2

def test_the_deck_vectors_are_computed_as_before_bit_for_bit() -> None:
    """Regression: stored runs reproduce only if the vectors don't change by rounding, so they're still the summed lines over their length, not lines @ E."""
    decks = [cards(Shock=4, Mountain=56), cards(Essence_Scatter=4, Island=56)]
    column = {name: i for i, name in enumerate(EMBEDDING.names)}
    raw = np.zeros((len(decks), len(EMBEDDING.names)))
    for r, deck in enumerate(decks):
        for line in deck:
            raw[r, column[line.card]] = math.sqrt(line.n) * WEIGHTS[line.card]
    summed = np.asarray(sparse.csr_matrix(raw) @ EMBEDDING.vectors.astype(np.float64))
    before = summed / np.linalg.norm(summed, axis=1, keepdims=True)
    assert np.array_equal(build_deck_vectors(decks, EMBEDDING, WEIGHTS.__getitem__, math.sqrt).matrix, before)
