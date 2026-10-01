from collections.abc import Iterator
from datetime import UTC, datetime

import pytest

from archetype_classifier.data_loading import loader
from archetype_classifier.data_loading.dataset import CardCount, split_decks
from archetype_classifier.data_loading.labels import LabelFacts, LabelStatus
from archetype_classifier.data_loading.splits import ExclusionReason, Split, SplitScheme
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


def test_a_snapshot_freezes_every_seeded_deck_with_its_label_facts(labelled_seed: Container, experiments_db: Database) -> None:
    validated, automatic, unlabelled = labelled_seed.deck_ids
    snapshot = loader.load_deck_facts(experiments_db, loader.create_snapshot(experiments_db))

    assert set(labelled_seed.deck_ids) <= set(snapshot.decks)
    labels = snapshot.decks[validated].labels
    assert (labels.human_archetype_id, labels.machine_archetype_id) == (labelled_seed.aggro_id, labelled_seed.aggro_id)
    assert labels.human_labelled_at == datetime.fromtimestamp(2, UTC) and labels.machine_labelled_at == datetime.fromtimestamp(1, UTC)
    assert snapshot.decks[validated].site_archetype_id == labelled_seed.aggro_id
    assert snapshot.decks[automatic].labels.human_archetype_id is None
    assert snapshot.decks[unlabelled].labels == LabelFacts(None, None, None, None)
    assert snapshot.decks[validated].maindeck_cards == 60
    assert snapshot.archetypes[labelled_seed.aggro_id].depth == 0

def test_a_later_relabel_does_not_change_a_snapshot(labelled_seed: Container, experiments_db: Database) -> None:
    validated = labelled_seed.deck_ids[0]
    snapshot_id = loader.create_snapshot(experiments_db)
    control_id = db().value("SELECT id FROM archetype WHERE name = 'Control'")
    db().execute('UPDATE deck SET archetype_id = %s WHERE id = %s', [control_id, validated])
    db().execute('INSERT INTO deck_archetype_change (changed_date, deck_id, archetype_id, person_id) VALUES (3, %s, %s, %s)', [validated, control_id, labelled_seed.person_id])

    deck = loader.load_deck_facts(experiments_db, snapshot_id).decks[validated]
    assert deck.site_archetype_id == labelled_seed.aggro_id
    assert deck.labels.human_archetype_id == labelled_seed.aggro_id

def test_a_snapshot_loads_back_with_every_decks_split_matching_the_pure_functions(labelled_seed: Container, experiments_db: Database) -> None:
    validated, automatic, unlabelled = labelled_seed.deck_ids
    snapshot_id = loader.create_snapshot(experiments_db)
    scheme = whole_seed_is_test(labelled_seed)
    scheme_id = loader.create_scheme(experiments_db, scheme)
    loader.materialise_split(experiments_db, snapshot_id, scheme_id)
    snapshot = loader.load_snapshot(experiments_db, snapshot_id, scheme_id)

    assert snapshot.scheme == scheme
    assert (snapshot.decks[validated].split, snapshot.decks[validated].label_status, snapshot.decks[validated].label_id) == (Split.TEST, LabelStatus.VERIFIED, labelled_seed.aggro_id)
    assert snapshot.decks[validated].unseen_maindeck_copies == 60  # No training decks, so every maindeck card is unseen.
    assert (snapshot.decks[automatic].split, snapshot.decks[automatic].exclusion_reason) == (Split.EXCLUDED, ExclusionReason.STATUS_NOT_EVALUATED)
    assert snapshot.decks[unlabelled].label_status == LabelStatus.UNVERIFIED  # Labelled on the site, but no history.
    pure = split_decks(loader.load_deck_facts(experiments_db, snapshot_id), loader.iter_deck_cards(), scheme)
    assert {i: (d.split, d.exclusion_reason, d.label_status, d.label_id, d.unseen_maindeck_copies) for i, d in snapshot.decks.items()} == \
           {i: (s.split, s.reason, s.label_status, s.label_id, s.unseen_maindeck_copies) for i, s in pure.decks.items()}


# Scenario: a large maindeck loads in full (Scenarios.md, "Splitting decks"). The real deck 217677 is checked once, in the rebuild verification.

@pytest.fixture
def life_is_ez_seed(labelled_seed: Container) -> Iterator[int]:
    """The first seeded deck enlarged to a 112-card maindeck (4 Lightning Bolt, 108 Mountain) and a 15-card sideboard, like deck 217677."""
    deck_id = labelled_seed.deck_ids[0]
    db().execute("UPDATE deck_card SET n = 108 WHERE deck_id = %s AND card = 'Mountain' AND NOT sideboard", [deck_id])
    db().execute("INSERT INTO deck_card (deck_id, card, n, sideboard) VALUES (%s, 'Smash to Smithereens', 15, TRUE)", [deck_id])
    try:
        yield deck_id
    finally:
        db().execute("DELETE FROM deck_card WHERE deck_id = %s AND sideboard", [deck_id])
        db().execute("UPDATE deck_card SET n = 56 WHERE deck_id = %s AND card = 'Mountain'", [deck_id])

def test_a_112_card_maindeck_loads_in_full(life_is_ez_seed: int, experiments_db: Database) -> None:
    contents = loader.load_contents([life_is_ez_seed])[life_is_ez_seed]
    assert sum(c.n for c in contents.maindeck) == 112
    assert sum(c.n for c in contents.sideboard) == 15
    assert CardCount('Mountain', 108) in contents.maindeck
    assert loader.load_deck_facts(experiments_db, loader.create_snapshot(experiments_db)).decks[life_is_ez_seed].maindeck_cards == 112
