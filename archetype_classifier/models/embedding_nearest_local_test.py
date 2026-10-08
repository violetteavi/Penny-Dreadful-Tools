"""The nearest deck on the saved combined embedding and real decks. Skipped unless PD_LOCAL_DATA=1: it needs snapshot 1 and scheme 1 in the experiments
database, the real site database and the saved embedding in embeddings/.

    PD_LOCAL_DATA=1 uv run --group archetypes pytest -s archetype_classifier/models/embedding_nearest_local_test.py
"""
import os

import pytest

from archetype_classifier.data_loading import loader
from archetype_classifier.data_loading.slices import Snapshot, build_deck_set
from archetype_classifier.data_loading.splits import Split
from archetype_classifier.evaluation.metrics import ArchetypeTree
from archetype_classifier.evaluation.model import FitContext, build_predict_decks, build_training_decks
from archetype_classifier.models.embedding_nearest import EmbeddingNearestDeck

pytestmark = pytest.mark.skipif(os.environ.get('PD_LOCAL_DATA') != '1', reason='needs the full local dump: set PD_LOCAL_DATA=1')
EMBEDDING = 'potion__masked__average__w0.5-0.1667-0.1667-0.1667__fit1-38__emb1-39'


@pytest.fixture(scope='module')
def snapshot() -> Snapshot:
    return loader.load_snapshot(loader.experiments_db(), 1, 1)

@pytest.fixture(scope='module')
def model(snapshot: Snapshot) -> EmbeddingNearestDeck:
    train = build_deck_set(snapshot, frozenset({Split.TRAIN}))
    model = EmbeddingNearestDeck({'embedding': EMBEDDING})
    model.fit(build_training_decks(train, loader.load_contents(train.decks)), [], FitContext(ArchetypeTree(snapshot.archetypes), {}, seed=0))
    return model


# Scenario: a deck identical to training decks copies their label (real data).

def test_deck_269508_copies_the_label_of_its_identical_training_decks(snapshot: Snapshot, model: EmbeddingNearestDeck) -> None:
    deck = snapshot.decks[269508]
    deck_set = build_deck_set(Snapshot({deck.deck_id: deck}, snapshot.archetypes, snapshot.scheme), frozenset({Split.VALIDATION}))
    [prediction] = model.predict(build_predict_decks(deck_set, loader.load_contents([deck.deck_id])))
    names = {a.id: a.name for a in snapshot.archetypes.values()}
    assert names[prediction.guess_id] == 'Oops All Lands'  # type: ignore[index]
    evidence = dict(prediction.evidence)
    assert names[evidence.pop('runner_up_id')] == "Tibalt's Trickery"  # type: ignore[index]
    assert evidence == {'match_deck_id': 264554, 'similarity': 1.0, 'match_decks': 2, 'tied_rows': 1, 'runner_up_similarity': 0.982405, 'embedded_copies': 60, 'skipped_copies': 0}

def test_scheme_1_makes_84094_training_rows_and_no_card_is_missing(model: EmbeddingNearestDeck) -> None:
    state = model.state()
    assert (state['training_rows'], state['skipped_copies'], state['decks_with_skipped_cards']) == (84094, 0, 0)
