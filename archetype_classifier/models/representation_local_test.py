"""Deck representations on real data (Scenarios.md, "Deck representations", and "Reference decks for every model"). Skipped unless PD_LOCAL_DATA=1: it
needs snapshot 1 and scheme 1 in the experiments database, run 8, the real site and cards databases and the saved embedding in embeddings/. It fits the
nearest deck v3 three ways and the bag of cards, which takes a few minutes.

    PD_LOCAL_DATA=1 uv run --group archetypes pytest -s archetype_classifier/models/representation_local_test.py
"""
import math
import os

import numpy as np
import pytest

from archetype_classifier.data_loading import loader
from archetype_classifier.data_loading.slices import Snapshot, build_deck_set
from archetype_classifier.data_loading.splits import Split
from archetype_classifier.evaluation.metrics import ArchetypeTree
from archetype_classifier.evaluation.model import FitContext, Model, Prediction, TrainingDeck, build_predict_decks, build_training_decks
from archetype_classifier.evaluation.reference_decks import REFERENCE_DECKS, Kind, build_hand_made_deck, build_reference_result, build_reference_table, load_reference_decks
from archetype_classifier.evaluation.reference_decks_local_test import JUDGED
from archetype_classifier.evaluation.store import load_guesses
from archetype_classifier.models.bag_nearest import BagNearestDeck
from archetype_classifier.models.card_weights import CardWeights, build_card_weights
from archetype_classifier.models.embedding_nearest import EmbeddingNearestDeck

pytestmark = pytest.mark.skipif(os.environ.get('PD_LOCAL_DATA') != '1', reason='needs the full local dump: set PD_LOCAL_DATA=1')
EMBEDDING = 'potion__masked__average__w0.5-0.1667-0.1667-0.1667__fit1-38__emb1-39'
NEW_MODELS: dict[str, Model] = {'run 10: bag of cards, idf, sqrt': BagNearestDeck({'copies': 'sqrt'}),
              'run 11: nearest deck, idf, sqrt': EmbeddingNearestDeck({'embedding': EMBEDDING, 'weights': 'idf', 'copies': 'sqrt'}),
              'run 12: nearest deck, idf, linear': EmbeddingNearestDeck({'embedding': EMBEDDING, 'weights': 'idf', 'copies': 'linear'})}


@pytest.fixture(scope='module')
def snapshot() -> Snapshot:
    return loader.load_snapshot(loader.experiments_db(), 1, 1)

@pytest.fixture(scope='module')
def training(snapshot: Snapshot) -> list[TrainingDeck]:
    train = build_deck_set(snapshot, frozenset({Split.TRAIN}))
    return build_training_decks(train, loader.load_contents(train.decks))

@pytest.fixture(scope='module')
def context(snapshot: Snapshot, training: list[TrainingDeck]) -> FitContext:
    return FitContext(ArchetypeTree(snapshot.archetypes), loader.load_legal_cards({d.season_id for d in training}), seed=0)

@pytest.fixture(scope='module')
def weights(training: list[TrainingDeck], context: FitContext) -> CardWeights:
    return build_card_weights(training, context.legal_cards)

@pytest.fixture(scope='module')
def models(training: list[TrainingDeck], context: FitContext) -> dict[str, Model]:
    for model in NEW_MODELS.values():
        model.fit(training, [], context)
    return dict(NEW_MODELS)


# Scenario: real card weights.

def test_real_card_weights(training: list[TrainingDeck], weights: CardWeights) -> None:
    assert len(training) == 162878
    real = {c: round(weights.weight(c), 4) for c in ('Island', 'Mountain', 'Burst Lightning', 'Nadu, Winged Wisdom', 'Make Disappear', 'A card never legal in seasons 1-38')}
    assert real == {'Island': 1.9825, 'Mountain': 2.1695, 'Burst Lightning': 3.1864, 'Nadu, Winged Wisdom': 3.4922, 'Make Disappear': 7.3559,
                    'A card never legal in seasons 1-38': 9.3634}
    assert (len(weights.idf), round(max(weights.idf.values()), 4), len(weights.outside_legal)) == (23618, 13.0008, 8)
    assert min(weights.idf, key=weights.idf.__getitem__) == 'Island'


# Not a scenario: the nearest deck v3 with no new parameters is run 8's model.

def test_version_3_with_default_parameters_reproduces_run_8_on_season_39(snapshot: Snapshot, training: list[TrainingDeck], context: FitContext) -> None:
    model = EmbeddingNearestDeck({'embedding': EMBEDDING})
    model.fit(training, [], context)
    validation = build_deck_set(snapshot, frozenset({Split.VALIDATION}))
    predictions = model.predict(build_predict_decks(validation, loader.load_contents(validation.decks)))
    stored = load_guesses(loader.experiments_db(), 8)
    assert len(predictions) == 2249
    assert [as_stored(p) for p in predictions] == [as_stored(stored[p.deck_id]) for p in predictions]  # Stored scores have 4 decimals.


def as_stored(p: Prediction) -> tuple[int | None, list[tuple[int, float | None]]]:
    return p.guess_id, [(c.archetype_id, None if c.score is None else round(c.score, 4)) for c in p.candidates or ()]


# Scenario: a deck of only newly legal cards (real data).

def test_the_deck_of_only_new_cards_under_each_representation(weights: CardWeights, models: dict[str, Model]) -> None:
    deck = build_hand_made_deck()
    assert {round(weights.weight(line.card), 4) for line in deck.maindeck} == {9.3634}
    bag, idf_sqrt, idf_linear = (m.predict([deck])[0] for m in models.values())
    assert (bag.guess_id, bag.candidates, bag.evidence) == (None, (), {'known_copies': 0, 'unseen_copies': 60})
    for prediction in (idf_sqrt, idf_linear):
        assert prediction.guess_id is not None and (prediction.evidence['embedded_copies'], prediction.evidence['skipped_copies']) == (60, 0)
    nearest = models['run 12: nearest deck, idf, linear']
    assert isinstance(nearest, EmbeddingNearestDeck)
    unweighted = EmbeddingNearestDeck({'embedding': EMBEDDING})
    unweighted.embedding = nearest.embedding
    assert np.allclose(nearest.deck_vectors([deck.maindeck]).matrix, unweighted.deck_vectors([deck.maindeck]).matrix)  # Equal weights don't turn the vector.
    assert not math.isnan(float(nearest.deck_vectors([deck.maindeck]).matrix.sum()))


# Scenario: reference decks for every model. The guards are asserted; the hard cases and the extreme are printed.

def test_the_reference_decks_under_the_new_models(snapshot: Snapshot, models: dict[str, Model]) -> None:
    decks = list(load_reference_decks(snapshot).values())
    ids = {a.name: a.id for a in snapshot.archetypes.values()}
    results = {name: {p.deck_id: build_reference_result(JUDGED[p.deck_id], p, ids) for p in model.predict(decks)} for name, model in models.items()}
    print('\n' + build_reference_table(results, {a.id: a.name for a in snapshot.archetypes.values()}))
    guards = [d.deck_id for d in REFERENCE_DECKS if d.kind == Kind.GUARD]
    assert {(m, i): r[i].passed for m, r in results.items() for i in guards} == {(m, i): True for m in results for i in guards}
