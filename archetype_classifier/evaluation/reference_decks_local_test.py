"""Reference decks on the existing models and real data (Scenarios.md, "Reference decks for every model"). Skipped unless PD_LOCAL_DATA=1: it needs
snapshot 1 with schemes 1 and 2 in the experiments database, runs 7-9, the real site and cards databases and the saved embeddings in embeddings/. It
fits the three models as runs 7-9 were fitted, which takes a few minutes, and prints the table a write-up carries.

    PD_LOCAL_DATA=1 uv run --group archetypes pytest -s archetype_classifier/evaluation/reference_decks_local_test.py
"""
import os
from collections.abc import Mapping

import pytest

from archetype_classifier.data_loading import loader
from archetype_classifier.data_loading.dataset import DeckContents
from archetype_classifier.data_loading.slices import Snapshot, build_deck_set
from archetype_classifier.data_loading.splits import Split
from archetype_classifier.evaluation.metrics import ArchetypeTree
from archetype_classifier.evaluation.model import FitContext, Model, Prediction, build_training_decks
from archetype_classifier.evaluation.reference_decks import GROUPS, HAND_MADE_ID, REFERENCE_DECKS, Kind, ReferenceResult, build_hand_made_deck, build_reference_result, build_reference_table, load_reference_decks
from archetype_classifier.evaluation.store import load_guesses
from archetype_classifier.models.embedding_nearest import EmbeddingNearestDeck
from archetype_classifier.models.similarity import SimilarityBaseline

pytestmark = pytest.mark.skipif(os.environ.get('PD_LOCAL_DATA') != '1', reason='needs the full local dump: set PD_LOCAL_DATA=1')
TEXT_ONLY = 'potion__masked__average__w1-0-0-0__fit1-38__emb1-39'
TEXT_AND_NUMBERS = 'potion__masked__average__w0.5-0.1667-0.1667-0.1667__fit1-38__emb1-39'
RUNS = {'run 7: nearest deck, text only': 7, 'run 8: nearest deck, text and numbers': 8, "run 9: site's guesser at 20": 9}
JUDGED = {**{d.deck_id: d for d in REFERENCE_DECKS}, **{i: next(d for d in REFERENCE_DECKS if d.deck_id == g) for g, group in GROUPS.items() for i in group}}


@pytest.fixture(scope='module')
def snapshots() -> dict[int, Snapshot]:
    edb = loader.experiments_db()
    return {scheme: loader.load_snapshot(edb, 1, scheme) for scheme in (1, 2)}

@pytest.fixture(scope='module')
def training_contents(snapshots: dict[int, Snapshot]) -> dict[int, DeckContents]:
    """Scheme 2's TRAIN decks, which include all of scheme 1's: loaded once for both."""
    assert {i for i, d in snapshots[1].decks.items() if d.split == Split.TRAIN} <= {i for i, d in snapshots[2].decks.items() if d.split == Split.TRAIN}
    return loader.load_contents(i for i, d in snapshots[2].decks.items() if d.split == Split.TRAIN)

@pytest.fixture(scope='module')
def models(snapshots: dict[int, Snapshot], training_contents: dict[int, DeckContents]) -> dict[str, Model]:
    """The three existing models, fitted as runs 7, 8 and 9 were."""
    fitted: dict[str, Model] = {}
    train_1 = build_training_decks(build_deck_set(snapshots[1], frozenset({Split.TRAIN})), training_contents)
    for name, embedding in zip(list(RUNS)[:2], (TEXT_ONLY, TEXT_AND_NUMBERS), strict=True):
        nearest = EmbeddingNearestDeck({'embedding': embedding})
        nearest.fit(train_1, [], FitContext(ArchetypeTree(snapshots[1].archetypes), {}, seed=0))
        fitted[name] = nearest
    train_2 = build_deck_set(snapshots[2], frozenset({Split.TRAIN}))
    baseline = SimilarityBaseline({'threshold': 20})
    baseline.fit(build_training_decks(train_2, training_contents), [],
                 FitContext(ArchetypeTree(snapshots[2].archetypes), loader.load_legal_cards({d.season_id for d in train_2.decks.values()}), seed=0))
    fitted[list(RUNS)[2]] = baseline
    return fitted

@pytest.fixture(scope='module')
def archetype_ids(snapshots: dict[int, Snapshot]) -> dict[str, int]:
    return {a.name: a.id for a in snapshots[1].archetypes.values()}

def judge(predictions: Mapping[int, Prediction], archetype_ids: Mapping[str, int]) -> dict[int, ReferenceResult]:
    return {i: build_reference_result(JUDGED[i], p, archetype_ids) for i, p in predictions.items() if i in JUDGED}

@pytest.fixture(scope='module')
def results(snapshots: dict[int, Snapshot], models: dict[str, Model], archetype_ids: dict[str, int]) -> dict[str, dict[int, ReferenceResult]]:
    decks = list(load_reference_decks(snapshots[1]).values())
    return {name: judge({p.deck_id: p for p in model.predict(decks)}, archetype_ids) for name, model in models.items()}


def test_every_label_names_exactly_one_archetype(snapshots: dict[int, Snapshot]) -> None:
    names = [a.name for a in snapshots[1].archetypes.values()]
    assert all(names.count(d.label) == 1 for d in REFERENCE_DECKS if d.label), [d.label for d in REFERENCE_DECKS if d.label and names.count(d.label) != 1]

def test_every_reference_deck_and_group_deck_is_predicted(results: dict[str, dict[int, ReferenceResult]]) -> None:
    assert all(set(r) == set(JUDGED) for r in results.values())


# Scenario: decks every current model gets right (guards).

def test_every_guard_passes_under_every_existing_model(results: dict[str, dict[int, ReferenceResult]]) -> None:
    guards = [d.deck_id for d in REFERENCE_DECKS if d.kind == Kind.GUARD]
    assert {(m, i): r[i].passed for m, r in results.items() for i in guards} == {(m, i): True for m in results for i in guards}


# Scenario: decks the current models get wrong (hard cases). They're recorded, not asserted, so this only checks that the refitted models reproduce runs 7-9.

def test_the_refitted_models_reproduce_runs_7_to_9_on_every_real_deck(results: dict[str, dict[int, ReferenceResult]], archetype_ids: dict[str, int]) -> None:
    edb = loader.experiments_db()
    for name, run_id in RUNS.items():
        stored = judge(load_guesses(edb, run_id), archetype_ids)
        assert {i: r for i, r in results[name].items() if i != HAND_MADE_ID} == stored, name

# Scenario: a deck of only newly legal cards (extreme).

def test_the_hand_made_deck_is_still_all_new(training_contents: dict[int, DeckContents]) -> None:
    legal = loader.load_legal_cards(range(1, 40))
    cards = {c.card for c in build_hand_made_deck().maindeck}
    assert {c: [s for s in legal if c in legal[s]] for c in cards} == {c: [39] for c in cards}
    assert [i for i, c in training_contents.items() if cards & {line.card for line in c.maindeck}] == []

def test_print_the_table(results: dict[str, dict[int, ReferenceResult]], snapshots: dict[int, Snapshot]) -> None:
    print('\n' + build_reference_table(results, {a.id: a.name for a in snapshots[1].archetypes.values()}))
