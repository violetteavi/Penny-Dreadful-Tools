"""The model and run store against a real experiments database. The site database is replaced at its boundary (deck contents and legal cards), so a deck "deleted from the site" is simply missing from the contents."""
import logging
import re
import time
from collections.abc import Iterable, Iterator, Mapping, Sequence
from typing import ClassVar

import pytest

from archetype_classifier.data_loading import loader
from archetype_classifier.data_loading.dataset import CardCount, DeckContents
from archetype_classifier.data_loading.labels import LabelStatus
from archetype_classifier.data_loading.slices import build_deck_set, deck_ids_hash
from archetype_classifier.data_loading.splits import Split, SplitScheme
from archetype_classifier.evaluation.metrics import ArchetypeTree
from archetype_classifier.evaluation.model import FitContext, LabelledDeck, Model, Prediction, TrainingDeck, build_labelled_decks, build_predict_decks, build_training_decks, register
from archetype_classifier.evaluation.store import ModelRecord, StoreConflict, canonical, load_model, save_model
from archetype_classifier.models.most_common import MostCommonArchetype
from shared.database import Database

AGGRO, CONTROL, AGGRO_CONTROL = 1, 2, 3
RED_DECK_WINS, AZORIUS_CONTROL, AZORIUS_TEMPO = 16, 49, 552
ARCHETYPES = [(AGGRO, 'Aggro', None, 0), (CONTROL, 'Control', None, 0), (AGGRO_CONTROL, 'Aggro-Control', None, 0),
              (RED_DECK_WINS, 'Red Deck Wins', AGGRO, 1), (AZORIUS_CONTROL, 'Azorius Control', CONTROL, 1), (AZORIUS_TEMPO, 'Azorius Tempo', AGGRO_CONTROL, 1)]

# The decks of "Storing models and runs" (Scenarios.md): 60-card lists legal in seasons 30 and 39.
RED = DeckContents((CardCount('Mountain', 56), CardCount('Shock', 4)), ())
BLUE = DeckContents((CardCount('Essence Scatter', 4), CardCount('Island', 56)), ())
NEGATE = DeckContents((CardCount('Island', 56), CardCount('Negate', 4)), ())
DECKS = {  # deck id -> season, split, status, label, cards
    101: (30, Split.TRAIN, LabelStatus.VERIFIED, RED_DECK_WINS, RED), 102: (30, Split.TRAIN, LabelStatus.VERIFIED, RED_DECK_WINS, RED),
    103: (30, Split.TRAIN, LabelStatus.VERIFIED, RED_DECK_WINS, RED), 104: (30, Split.TRAIN, LabelStatus.VERIFIED, AZORIUS_CONTROL, BLUE),
    105: (30, Split.TRAIN, LabelStatus.VERIFIED, AZORIUS_CONTROL, BLUE), 201: (39, Split.VALIDATION, LabelStatus.VERIFIED, RED_DECK_WINS, RED),
    202: (39, Split.VALIDATION, LabelStatus.VERIFIED, AZORIUS_CONTROL, BLUE),
}
TRAIN, VALIDATION = frozenset({Split.TRAIN}), frozenset({Split.VALIDATION})


def store_snapshot(edb: Database, snapshot_id: int, scheme_id: int, decks: Mapping[int, tuple[int, Split, LabelStatus, int | None, DeckContents]]) -> None:
    """Write a snapshot and its splits under one scheme straight into the experiments database, as materialise_split would."""
    edb.execute('INSERT INTO snapshot (id, deck_count, max_deck_id, notes) VALUES (%s, %s, %s, %s)', [snapshot_id, len(decks), max(decks), 'test'])
    loader.insert_rows(edb, 'archetype_snapshot', ['snapshot_id', 'archetype_id', 'name', 'parent_id', 'depth'], [[snapshot_id, *a] for a in ARCHETYPES])
    loader.insert_rows(edb, 'deck_snapshot', ['snapshot_id', *loader.DECK_FACT_COLUMNS],
                       [[snapshot_id, i, season, 'League', True, f'{i:040x}', 60, None, None, None, None, label] for i, (season, _, _, label, _) in decks.items()])
    loader.insert_rows(edb, 'deck_split', ['snapshot_id', 'scheme_id', 'deck_id', 'split', 'exclusion_reason', 'label_status', 'label_id', 'unseen_maindeck_copies'],
                       [[snapshot_id, scheme_id, i, split.value, None, status.value, label, 0] for i, (_, split, status, label, _) in decks.items()])

class Site:
    """The site database's deck contents and legal cards. Deleting a deck makes its contents missing."""
    def __init__(self, contents: dict[int, DeckContents]) -> None:
        self.contents = dict(contents)

    def delete(self, *deck_ids: int) -> None:
        for i in deck_ids:
            del self.contents[i]

    def load_contents(self, deck_ids: Iterable[int]) -> dict[int, DeckContents]:
        return {i: self.contents[i] for i in deck_ids if i in self.contents}

@pytest.fixture
def site(experiments_db: Database, monkeypatch: pytest.MonkeyPatch) -> Iterator[Site]:
    """Snapshot 1 under scheme 1 (the typical scheme) holding the scenario decks, and a site serving their contents."""
    loader.ensure_schema(experiments_db)
    scheme_id = loader.create_scheme(experiments_db, SplitScheme('typical'))
    store_snapshot(experiments_db, 1, scheme_id, DECKS)
    site = Site({i: deck[4] for i, deck in DECKS.items()})
    monkeypatch.setattr(loader, 'load_contents', site.load_contents)
    monkeypatch.setattr(loader, 'load_legal_cards', lambda season_ids: {s: frozenset() for s in season_ids})
    yield site

def fit(edb: Database, model: Model, snapshot_id: int = 1, scheme_id: int = 1, seed: int = 0, training_splits: frozenset[Split] = TRAIN,
        validation_splits: frozenset[Split] = VALIDATION) -> ModelRecord:
    """Fit a model the way an experiment does, by composing the existing functions, and return its record."""
    snapshot = loader.load_snapshot(edb, snapshot_id, scheme_id)
    training_set, validation_set = build_deck_set(snapshot, training_splits), build_deck_set(snapshot, validation_splits)
    training = build_training_decks(training_set, loader.load_contents(training_set.decks))
    validation = build_labelled_decks(validation_set, loader.load_contents(validation_set.decks))
    context = FitContext(ArchetypeTree(snapshot.archetypes), loader.load_legal_cards({d.season_id for d in snapshot.decks.values()}), seed)
    start = time.perf_counter()
    model.fit(training, validation, context)
    return ModelRecord(model.name, model.version, model.params, snapshot_id, scheme_id, seed, training_splits, validation_splits,
                       len(training), deck_ids_hash(d.deck.deck_id for d in training), len(validation), deck_ids_hash(d.deck.deck_id for d in validation),
                       time.perf_counter() - start)

def validation_predictions(edb: Database, model: Model) -> list[Prediction]:
    validation_set = build_deck_set(loader.load_snapshot(edb, 1, 1), VALIDATION)
    return model.predict(build_predict_decks(validation_set, loader.load_contents(validation_set.decks)))


# Scenario: a saved model loads back and predicts the same.

def test_a_saved_model_loads_back_and_predicts_the_same(experiments_db: Database, site: Site, caplog: pytest.LogCaptureFixture) -> None:
    model = MostCommonArchetype({})
    record = fit(experiments_db, model)
    assert (record.training_count, record.training_hash) == (5, deck_ids_hash([101, 102, 103, 104, 105]))
    assert (record.validation_count, record.validation_hash) == (2, deck_ids_hash([201, 202]))
    assert save_model(experiments_db, model, record) == 1

    with caplog.at_level(logging.WARNING):
        loaded_record, loaded = load_model(experiments_db, 1)
    assert loaded_record == record
    assert loaded.state() == model.state() == {'archetype_id': RED_DECK_WINS, 'training_decks_with_archetype': 3, 'training_decks': 5}
    assert validation_predictions(experiments_db, loaded) == validation_predictions(experiments_db, model)
    assert caplog.text == ''


# Scenario: saving the same model again returns its id.

def test_saving_the_same_model_again_returns_its_id(experiments_db: Database, site: Site, caplog: pytest.LogCaptureFixture) -> None:
    first = MostCommonArchetype({})
    assert save_model(experiments_db, first, fit(experiments_db, first)) == 1
    again = MostCommonArchetype({})
    with caplog.at_level(logging.WARNING):
        assert save_model(experiments_db, again, fit(experiments_db, again)) == 1
    assert caplog.text == ''
    other_seed = MostCommonArchetype({})
    assert save_model(experiments_db, other_seed, fit(experiments_db, other_seed, seed=1)) == 2  # Nothing was stored in between.


# Scenario: a fit that isn't deterministic fails loudly.

@register
class Unrepeatable(MostCommonArchetype):
    """A stand-in model whose fit ignores the seed: every fit learns something different."""
    name: ClassVar[str] = 'unrepeatable (test)'
    fits = 0

    def fit(self, training: Sequence[TrainingDeck], validation: Sequence[LabelledDeck], context: FitContext) -> None:
        super().fit(training, validation, context)
        Unrepeatable.fits += 1
        self.training_decks += Unrepeatable.fits  # Stands in for a random draw the seed doesn't control.

def test_a_fit_that_isnt_deterministic_fails_loudly(experiments_db: Database, site: Site) -> None:
    first = Unrepeatable({})
    assert save_model(experiments_db, first, fit(experiments_db, first)) == 1
    second = Unrepeatable({})
    second_record = fit(experiments_db, second)
    with pytest.raises(StoreConflict, match=r'model 1.*' + re.escape(canonical(first.state())) + '.*' + re.escape(canonical(second.state()))):
        save_model(experiments_db, second, second_record)
    other_seed = Unrepeatable({})
    assert save_model(experiments_db, other_seed, fit(experiments_db, other_seed, seed=1)) == 2  # Nothing was stored.


# Scenario: training data that changed underneath gives a new model and a warning.

def test_training_data_that_changed_underneath_gives_a_new_model_and_a_warning(experiments_db: Database, site: Site, caplog: pytest.LogCaptureFixture) -> None:
    original = MostCommonArchetype({})
    assert save_model(experiments_db, original, fit(experiments_db, original)) == 1
    site.delete(101, 102)  # Two of the three Red Deck Wins decks.

    refit = MostCommonArchetype({})
    record = fit(experiments_db, refit)
    assert record.training_count == 3
    assert {p.guess_id for p in validation_predictions(experiments_db, refit)} == {AZORIUS_CONTROL}
    with caplog.at_level(logging.WARNING):
        assert save_model(experiments_db, refit, record) == 2
    assert 'training decks changed since model 1' in caplog.text and 'model 1 can no longer be reproduced' in caplog.text

    caplog.clear()
    with caplog.at_level(logging.WARNING):
        _, reloaded = load_model(experiments_db, 1)
    assert {p.guess_id for p in validation_predictions(experiments_db, reloaded)} == {RED_DECK_WINS}
    assert 'Model 1 is not reproducible: it trained on 5 decks' in caplog.text and 'now rebuild as 3' in caplog.text
