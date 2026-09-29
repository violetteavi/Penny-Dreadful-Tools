from collections.abc import Iterator

import pytest

from archetype_classifier.data_loading import loader
from archetype_classifier.data_loading.labels import Provenance
from archetype_classifier.data_loading.splits import Split, SplitScheme
from decksite.conftest import seeded_db  # noqa: F401  # The repo's seeded site database, reused as-is.
from decksite.database import db
from shared.container import Container
from shared.database import Database, get_database

EXPERIMENTS_TEST_DB = 'archetype_experiments_test'


@pytest.fixture
def experiments_db() -> Iterator[Database]:
    edb = get_database(EXPERIMENTS_TEST_DB)
    edb.execute(f'DROP DATABASE IF EXISTS {EXPERIMENTS_TEST_DB}')
    edb.execute(f'CREATE DATABASE {EXPERIMENTS_TEST_DB} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
    edb.execute(f'USE {EXPERIMENTS_TEST_DB}')
    yield edb
    edb.execute(f'DROP DATABASE IF EXISTS {EXPERIMENTS_TEST_DB}')

@pytest.fixture
def labelled_seed(seeded_db: Container) -> Iterator[Container]:  # noqa: F811
    """The seeded decks with a validated guess, an unreviewed guess and no history. Restores the shared seed afterwards."""
    validated, automatic, _ = seeded_db.deck_ids
    aggro_id = db().value("SELECT id FROM archetype WHERE name = 'Aggro'")
    person_id = seeded_db.person_id
    db().execute('INSERT INTO deck_archetype_change (changed_date, deck_id, archetype_id, person_id) VALUES (1, %s, %s, NULL), (2, %s, %s, %s), (1, %s, %s, NULL)',
                 [validated, aggro_id, validated, aggro_id, person_id, automatic, aggro_id])
    season_id = db().value('SELECT season_id FROM deck_cache WHERE deck_id = %s', [validated])
    try:
        yield Container({**seeded_db, 'aggro_id': aggro_id, 'season_id': season_id})
    finally:
        db().execute('DELETE FROM deck_archetype_change WHERE deck_id IN %s', [tuple(seeded_db.deck_ids)])
        db().execute('UPDATE deck SET archetype_id = %s WHERE id = %s', [aggro_id, validated])

def whole_seed_is_test(seed: Container) -> SplitScheme:
    return SplitScheme('integration', train_seasons=frozenset(), validation_seasons=frozenset(), test_seasons=frozenset({seed.season_id}))


def test_a_snapshot_and_scheme_load_back_as_a_dataset(labelled_seed: Container, experiments_db: Database) -> None:
    validated, automatic, unlabelled = labelled_seed.deck_ids
    snapshot_id = loader.create_snapshot(experiments_db)
    scheme_id = loader.create_scheme(experiments_db, whole_seed_is_test(labelled_seed))
    loader.materialise_split(experiments_db, snapshot_id, scheme_id)
    dataset = loader.load_dataset(experiments_db, snapshot_id, scheme_id)

    assert set(dataset.decks) == set(labelled_seed.deck_ids)
    assert dataset.decks[validated].provenance == Provenance.VALIDATED_GUESS
    assert dataset.decks[validated].ground_truth
    assert dataset.decks[validated].archetype_id == labelled_seed.aggro_id
    assert dataset.decks[automatic].provenance == Provenance.AUTOMATIC
    assert not dataset.decks[automatic].ground_truth
    assert dataset.decks[unlabelled].provenance == Provenance.NO_HISTORY
    assert {d.split for d in dataset.decks.values()} == {Split.TEST}
    assert {d.unseen_maindeck_copies for d in dataset.decks.values()} == {60}  # No training decks, so every maindeck card is unseen.
    assert dataset.archetypes[labelled_seed.aggro_id].depth == 0

def test_a_later_relabel_does_not_change_a_snapshot(labelled_seed: Container, experiments_db: Database) -> None:
    validated = labelled_seed.deck_ids[0]
    snapshot_id = loader.create_snapshot(experiments_db)
    scheme_id = loader.create_scheme(experiments_db, whole_seed_is_test(labelled_seed))
    loader.materialise_split(experiments_db, snapshot_id, scheme_id)
    control_id = db().value("SELECT id FROM archetype WHERE name = 'Control'")
    db().execute('UPDATE deck SET archetype_id = %s WHERE id = %s', [control_id, validated])
    db().execute('INSERT INTO deck_archetype_change (changed_date, deck_id, archetype_id, person_id) VALUES (3, %s, %s, %s)', [validated, control_id, labelled_seed.person_id])

    dataset = loader.load_dataset(experiments_db, snapshot_id, scheme_id)
    assert dataset.decks[validated].archetype_id == labelled_seed.aggro_id
    assert dataset.decks[validated].provenance == Provenance.VALIDATED_GUESS
