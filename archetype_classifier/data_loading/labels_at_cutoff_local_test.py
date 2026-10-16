"""Labels at a cutoff (#59) on the full local dump. Skipped unless PD_LOCAL_DATA=1: it needs snapshot 1 with its label history, and schemes 1 and 3.

    PD_LOCAL_DATA=1 uv run pytest -s archetype_classifier/data_loading/labels_at_cutoff_local_test.py
"""
import os
from collections import Counter

import pytest

from archetype_classifier.data_loading import loader
from archetype_classifier.data_loading.dataset import split_decks
from archetype_classifier.data_loading.slices import Snapshot
from archetype_classifier.data_loading.splits import Split
from archetype_classifier.evaluation.rows import build_relabelled

pytestmark = pytest.mark.skipif(os.environ.get('PD_LOCAL_DATA') != '1', reason='needs the full local dump: set PD_LOCAL_DATA=1')

SNAPSHOT_ID = 1
NEW_SINCE_THE_CUTOFF = ('Izzet Madcap', 'Solemnity Aristocrats', 'Flare Deck Wins', 'Through the Breach')


def scheme_id(name: str) -> int:
    return int(loader.experiments_db().value('SELECT id FROM split_scheme WHERE name = %s', [name]))

@pytest.fixture(scope='module')
def today() -> Snapshot:
    return loader.load_snapshot(loader.experiments_db(), SNAPSHOT_ID, scheme_id('default'))

@pytest.fixture(scope='module')
def at_season_39() -> Snapshot:
    return loader.load_snapshot(loader.experiments_db(), SNAPSHOT_ID, scheme_id('default, labels at season 39'))


# Scenario: snapshot 1 at season 39's start (Scenarios.md, "Labels at a cutoff").

def test_the_split_report_counts_the_training_decks_decided_after_the_cutoff(at_season_39: Snapshot) -> None:
    edb = loader.experiments_db()
    splits = split_decks(loader.load_deck_facts(edb, SNAPSHOT_ID), loader.iter_deck_cards(), at_season_39.scheme, loader.load_snapshot_history(edb, SNAPSHOT_ID))
    assert splits.report.cutoff_labels == Counter({'different label': 203, 'same label': 8, 'no label': 9, 'out of scope': 2})

def test_train_loses_the_decks_with_no_label_at_the_cutoff(today: Snapshot, at_season_39: Snapshot) -> None:
    train = [i for i, d in at_season_39.decks.items() if d.split == Split.TRAIN]
    assert len(train) == 162_869
    assert len([d for d in today.decks.values() if d.split == Split.TRAIN]) == 162_878
    assert sum(1 for i in train if at_season_39.decks[i].label_id != today.decks[i].label_id) == 203

def test_archetypes_created_after_the_cutoff_have_no_training_decks(today: Snapshot, at_season_39: Snapshot) -> None:
    ids = {a.id: a.name for a in at_season_39.archetypes.values() if a.name in NEW_SINCE_THE_CUTOFF}
    assert sorted(ids.values()) == sorted(NEW_SINCE_THE_CUTOFF)
    def counts(snapshot: Snapshot) -> Counter[str]:
        return Counter(ids[d.label_id] for d in snapshot.decks.values() if d.split == Split.TRAIN and d.label_id in ids)
    assert counts(at_season_39) == Counter()
    assert counts(today) == Counter({'Through the Breach': 58, 'Flare Deck Wins': 26, 'Izzet Madcap': 3, 'Solemnity Aristocrats': 1})

def test_scored_decks_keep_their_splits_and_labels(today: Snapshot, at_season_39: Snapshot) -> None:
    def scored(snapshot: Snapshot) -> dict[int, tuple[Split, int | None]]:
        return {i: (d.split, d.label_id) for i, d in snapshot.decks.items() if d.split in (Split.HELD_OUT, Split.VALIDATION, Split.TEST)}
    assert scored(at_season_39) == scored(today)

def test_eighty_season_39_decks_were_relabelled_after_the_season(at_season_39: Snapshot) -> None:
    validation = [d for d in at_season_39.decks.values() if d.split == Split.VALIDATION]
    assert len(build_relabelled(validation, loader.load_snapshot_history(loader.experiments_db(), SNAPSHOT_ID), loader.load_season_starts())) == 80
