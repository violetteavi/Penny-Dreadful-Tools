"""The nearest deck on the bag of cards, on rule-level decks (Scenarios.md, "Deck representations"). Real data is checked in representation_local_test.py."""
import dataclasses
import math
from collections.abc import Callable, Mapping, Sequence

import numpy as np
import pytest

from archetype_classifier.card_embeddings.deck_vectors_test import cards
from archetype_classifier.data_loading.dataset import CardCount
from archetype_classifier.evaluation.metrics import ArchetypeTree
from archetype_classifier.evaluation.model import FitContext, PredictDeck, Prediction, TrainingDeck, model_class
from archetype_classifier.models.bag_nearest import BagNearestDeck, build_bag_vectors, build_vocabulary
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


# The model: the nearest training row on the bag of cards. The card-weight scenario's training decks, with deck 6 ("4 Burst Lightning, 56 Mountain")
# relabelled Mono Red Swarm. Rows: "4 Shock, 56 Mountain" Red Deck Wins (3 decks), "4 Negate, 56 Island" and "4 Essence Scatter, 56 Island" Azorius
# Control, and R2 Mono Red Swarm.

RED_DECK_WINS, MONO_RED_SWARM, AZORIUS_CONTROL = 16, 164, 49
BAG_TRAINING = [dataclasses.replace(d, archetype_id=MONO_RED_SWARM) if d.deck.deck_id == 6 else d for d in TRAINING]
TREE = ArchetypeTree({})

def fitted(training: Sequence[TrainingDeck] = BAG_TRAINING, legal: Mapping[int, frozenset[str]] = LEGAL) -> BagNearestDeck:
    model = BagNearestDeck({'copies': 'sqrt'})
    model.fit(training, [], FitContext(TREE, legal, seed=0))
    return model

def query(deck_id: int, maindeck: tuple[CardCount, ...]) -> PredictDeck:
    return PredictDeck(deck_id, 'League', maindeck, ())

def test_the_model_is_found_by_its_name() -> None:
    assert model_class('bag of cards nearest deck') is BagNearestDeck
    assert BagNearestDeck.version == 1

def test_unknown_copies_are_refused() -> None:
    with pytest.raises(ValueError, match='copies must be one of'):
        BagNearestDeck({'copies': 'log'})

def test_the_rarer_shared_card_decides_the_guess() -> None:
    [prediction] = fitted().predict([query(201, Q)])
    assert dataclasses.replace(prediction, candidates=None) == Prediction(201, MONO_RED_SWARM, {
        'match_deck_id': 6, 'similarity': 0.96039, 'match_decks': 1, 'tied_rows': 1, 'runner_up_id': RED_DECK_WINS, 'runner_up_similarity': 0.922905,
        'known_copies': 60, 'unseen_copies': 0})
    assert prediction.candidates is not None
    assert [(c.archetype_id, round(c.score or 0, 4)) for c in prediction.candidates] == [(MONO_RED_SWARM, 0.9604), (RED_DECK_WINS, 0.9229), (AZORIUS_CONTROL, 0.0)]

def test_an_unseen_card_keeps_the_guess_and_is_counted() -> None:
    [prediction] = fitted().predict([query(202, cards(Burst_Lightning=4, Shock=4, Mountain=52, Smaug_s_Fury=4))])
    assert (prediction.guess_id, prediction.evidence['similarity'], prediction.evidence['runner_up_similarity']) == (MONO_RED_SWARM, 0.89136, 0.856569)
    assert (prediction.evidence['known_copies'], prediction.evidence['unseen_copies']) == (60, 4)

def test_a_deck_with_no_known_card_gets_no_guess() -> None:
    [prediction] = fitted().predict([query(203, cards(Smaug_s_Fury=4, Divination=4))])
    assert prediction == Prediction(203, None, {'known_copies': 0, 'unseen_copies': 8}, ())

def test_with_no_training_rows_no_deck_gets_a_guess() -> None:
    model = fitted([dataclasses.replace(d, archetype_id=None) for d in BAG_TRAINING])
    assert model.predict([query(201, Q)]) == [Prediction(201, None, {'known_copies': 0, 'unseen_copies': 60}, ())]


# Scenario: candidates and ties follow the nearest-deck rules.

def test_an_identical_maindeck_labelled_twice_goes_to_the_label_with_more_decks() -> None:
    training = [*BAG_TRAINING, dataclasses.replace(BAG_TRAINING[0], deck=dataclasses.replace(BAG_TRAINING[0].deck, deck_id=9), archetype_id=MONO_RED_SWARM)]
    [prediction] = fitted(training).predict([query(204, R1)])
    assert (prediction.guess_id, prediction.evidence['tied_rows'], prediction.evidence['match_decks']) == (RED_DECK_WINS, 2, 3)
    assert prediction.candidates is not None
    assert [c.archetype_id for c in prediction.candidates][:2] == [RED_DECK_WINS, MONO_RED_SWARM]


# Scenario: fitted models load back, and refuse changed weights.

def test_the_state_records_the_rows_vocabulary_and_card_weights_never_vectors() -> None:
    assert fitted().state() == {'training_decks': 8, 'training_rows': 4, 'vocabulary': 6, 'card_weights': build_card_weights(BAG_TRAINING, LEGAL).summary()}

def test_a_fitted_model_loads_back_and_guesses_the_same() -> None:
    model = fitted()
    decks = [query(201, Q), query(202, cards(Essence_Scatter=4, Negate=4, Island=52))]
    loaded = BagNearestDeck.from_state(model.params, model.state(), BAG_TRAINING, FitContext(TREE, LEGAL, seed=0))
    assert loaded.predict(decks) == model.predict(decks)
    assert loaded.state() == model.state()

def test_changed_card_weights_are_refused_naming_both_hashes() -> None:
    model = fitted()
    changed = {30: LEGAL[30], 31: LEGAL[31] - {'Divination'}}
    before, after = build_card_weights(BAG_TRAINING, LEGAL).hash(), build_card_weights(BAG_TRAINING, changed).hash()
    with pytest.raises(ValueError, match=f'card weights.*{before}.*{after}'):
        BagNearestDeck.from_state(model.params, model.state(), BAG_TRAINING, FitContext(TREE, changed, seed=0))
