"""The nearest deck on the bag of cards, on rule-level decks (Scenarios.md, "Deck representations"). Real data is checked in representation_local_test.py."""
import math
from collections.abc import Callable

import numpy as np
import pytest

from archetype_classifier.card_embeddings.deck_vectors_test import cards
from archetype_classifier.data_loading.dataset import CardCount
from archetype_classifier.models.bag_nearest import build_bag_vectors, build_vocabulary
from archetype_classifier.models.card_weights import build_card_weights
from archetype_classifier.models.card_weights_test import LEGAL, TRAINING

WEIGHTS = build_card_weights(TRAINING, LEGAL).weight
R1, R2 = cards(Shock=4, Mountain=56), cards(Burst_Lightning=4, Mountain=56)  # Red Deck Wins and Mono Red Swarm.
Q = cards(Burst_Lightning=4, Shock=4, Mountain=52)
VOCABULARY = build_vocabulary([R1, R2])


def cosines(deck: tuple[CardCount, ...], weight: Callable[[str], float] = WEIGHTS, copies: Callable[[int], float] = math.sqrt) -> list[float]:
    rows = build_bag_vectors([R1, R2], VOCABULARY, weight, copies)
    query = build_bag_vectors([deck], VOCABULARY, weight, copies)
    return [round(float(c), 5) for c in (query.matrix @ rows.matrix.T).toarray()[0]]


def test_the_vocabulary_is_every_card_the_rows_play_in_name_order() -> None:
    assert VOCABULARY == {'Burst Lightning': 0, 'Mountain': 1, 'Shock': 2}


# Scenario: the bag of cards: rarer shared cards decide.

def test_with_every_weight_1_and_linear_copies_the_two_rows_tie() -> None:
    assert cosines(Q, lambda card: 1.0, float) == [0.99706, 0.99706]

def test_card_weights_with_linear_copies_favour_the_rarer_shared_card() -> None:
    assert [round(c, 4) for c in cosines(Q, copies=float)] == [0.9928, 0.9962]

def test_card_weights_with_square_root_copies_favour_it_more() -> None:
    assert [round(c, 4) for c in cosines(Q)] == [0.9229, 0.9604]

def test_quantity_near_misses_count_partly() -> None:
    rows = build_bag_vectors([R1], VOCABULARY, WEIGHTS, math.sqrt)
    decks = build_bag_vectors([cards(Shock=1, Mountain=59), cards(Mountain=60)], VOCABULARY, WEIGHTS, math.sqrt)
    assert [round(float(c), 4) for c in (decks.matrix @ rows.matrix.T).toarray()[:, 0]] == [0.9890, 0.9565]

def test_two_different_cards_never_match() -> None:
    vocabulary = build_vocabulary([cards(Shock=4, Mountain=56)])
    rows = build_bag_vectors([cards(Shock=4, Mountain=56)], vocabulary, WEIGHTS, math.sqrt)
    deck = build_bag_vectors([cards(Burst_Lightning=4, Island=56)], vocabulary, WEIGHTS, math.sqrt)
    assert (deck.matrix @ rows.matrix.T).toarray()[0, 0] == 0


# Scenario: in the bag of cards, an unseen card lowers every similarity alike; a deck with no known card gets no guess.

def test_an_unseen_card_lowers_every_similarity_by_the_same_factor() -> None:
    with_fury = cards(Burst_Lightning=4, Shock=4, Mountain=52, Smaug_s_Fury=4)
    assert [round(c, 4) for c in cosines(with_fury)] == [0.8566, 0.8914]
    ratios = np.array(cosines(with_fury)) / np.array(cosines(Q))
    assert ratios[0] == pytest.approx(ratios[1], rel=1e-4)
    vectors = build_bag_vectors([with_fury], VOCABULARY, WEIGHTS, math.sqrt)
    assert (vectors.known.tolist(), vectors.unseen.tolist()) == ([60], [4])

def test_a_deck_of_only_unseen_cards_has_an_empty_row() -> None:
    vectors = build_bag_vectors([cards(Smaug_s_Fury=4, Divination=4)], VOCABULARY, WEIGHTS, math.sqrt)
    assert vectors.matrix.nnz == 0
    assert (vectors.known.tolist(), vectors.unseen.tolist()) == ([0], [8])

def test_rows_are_unit_length_and_no_decks_give_an_empty_matrix() -> None:
    rows = build_bag_vectors([R1, R2], VOCABULARY, WEIGHTS, math.sqrt)
    assert np.allclose(np.sqrt(rows.matrix.multiply(rows.matrix).sum(axis=1)).A.ravel(), 1)
    assert build_bag_vectors([], VOCABULARY, WEIGHTS, math.sqrt).matrix.shape == (0, 3)
