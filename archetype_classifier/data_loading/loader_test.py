import ast
import sys
from collections.abc import Iterator
from datetime import UTC, datetime

import pytest

from archetype_classifier.data_loading import loader
from archetype_classifier.data_loading.dataset import CardCount, split_decks
from archetype_classifier.data_loading.labels import LabelChange, LabelFacts, LabelStatus
from archetype_classifier.data_loading.splits import ExclusionReason, Split, SplitScheme
from decksite.conftest import seeded_db  # noqa: F401  # The repo's seeded site database, reused as-is.
from decksite.database import db
from shared.container import Container
from shared.database import Database


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



# Scenarios: labels at a cutoff (Scenarios.md). The snapshot keeps every deck's label history, oldest first.

def test_a_snapshot_keeps_every_decks_label_history_in_order(labelled_seed: Container, experiments_db: Database) -> None:
    validated, automatic, unlabelled = labelled_seed.deck_ids
    history = loader.load_snapshot_history(experiments_db, loader.create_snapshot(experiments_db))
    assert history[validated] == (LabelChange(validated, labelled_seed.aggro_id, by_person=False, changed_at=datetime.fromtimestamp(1, UTC)),
                                  LabelChange(validated, labelled_seed.aggro_id, by_person=True, changed_at=datetime.fromtimestamp(2, UTC)))
    assert history[automatic] == (LabelChange(automatic, labelled_seed.aggro_id, by_person=False, changed_at=datetime.fromtimestamp(1, UTC)),)
    assert unlabelled not in history

def test_label_history_is_added_to_a_snapshot_taken_without_it(labelled_seed: Container, experiments_db: Database) -> None:
    snapshot_id = loader.create_snapshot(experiments_db)
    expected = loader.load_snapshot_history(experiments_db, snapshot_id)
    experiments_db.execute('DELETE FROM label_change_snapshot WHERE snapshot_id = %s', [snapshot_id])  # As snapshot 1 was taken.
    assert loader.create_label_history(experiments_db, snapshot_id) == 3
    assert loader.load_snapshot_history(experiments_db, snapshot_id) == expected


def test_history_of_decks_outside_the_snapshot_is_not_kept(labelled_seed: Container, experiments_db: Database) -> None:
    validated = labelled_seed.deck_ids[0]
    snapshot_id = loader.create_snapshot(experiments_db)
    experiments_db.execute('DELETE FROM label_change_snapshot WHERE snapshot_id = %s', [snapshot_id])
    at_1 = datetime.fromtimestamp(1, UTC)
    history = [LabelChange(validated, labelled_seed.aggro_id, by_person=True, changed_at=at_1), LabelChange(-5, labelled_seed.aggro_id, by_person=True, changed_at=at_1)]
    assert loader.save_label_history(experiments_db, snapshot_id, history, frozenset({validated})) == 1
    assert set(loader.load_snapshot_history(experiments_db, snapshot_id)) == {validated}

# Scenario: adding history to a snapshot refuses a changed dump.

def test_adding_history_refuses_a_snapshot_that_already_has_it(labelled_seed: Container, experiments_db: Database) -> None:
    snapshot_id = loader.create_snapshot(experiments_db)
    with pytest.raises(ValueError, match='already has'):
        loader.create_label_history(experiments_db, snapshot_id)

def test_adding_history_refuses_a_dump_changed_since_the_snapshot(labelled_seed: Container, experiments_db: Database) -> None:
    validated = labelled_seed.deck_ids[0]
    snapshot_id = loader.create_snapshot(experiments_db)
    experiments_db.execute('DELETE FROM label_change_snapshot WHERE snapshot_id = %s', [snapshot_id])
    db().execute('INSERT INTO deck_archetype_change (changed_date, deck_id, archetype_id, person_id) VALUES (3, %s, %s, %s)', [validated, labelled_seed.aggro_id, labelled_seed.person_id])
    with pytest.raises(ValueError, match='latest label change') as refused:
        loader.create_label_history(experiments_db, snapshot_id)
    assert 'largest deck id' in str(refused.value)
    assert loader.load_snapshot_history(experiments_db, snapshot_id) == {}

def test_a_scheme_with_a_cutoff_splits_with_the_snapshots_history(labelled_seed: Container, experiments_db: Database) -> None:
    validated, automatic, _ = labelled_seed.deck_ids
    snapshot_id = loader.create_snapshot(experiments_db)
    cutoff_between = SplitScheme('integration at 1', train_seasons=frozenset({labelled_seed.season_id}), validation_seasons=frozenset(), test_seasons=frozenset(),
                                 held_out_percent=0, label_cutoff=1)  # The validated deck's person label (at 2) came after it.
    scheme_id = loader.create_scheme(experiments_db, cutoff_between)
    loader.materialise_split(experiments_db, snapshot_id, scheme_id)
    snapshot = loader.load_snapshot(experiments_db, snapshot_id, scheme_id)
    assert snapshot.scheme == cutoff_between
    assert (snapshot.decks[validated].label_status, snapshot.decks[validated].split) == (LabelStatus.UNVERIFIED, Split.EXCLUDED)
    assert (snapshot.decks[automatic].label_status, snapshot.decks[automatic].split) == (LabelStatus.UNVERIFIED, Split.EXCLUDED)

def test_a_scheme_with_a_cutoff_refuses_a_snapshot_without_history(labelled_seed: Container, experiments_db: Database) -> None:
    snapshot_id = loader.create_snapshot(experiments_db)
    experiments_db.execute('DELETE FROM label_change_snapshot WHERE snapshot_id = %s', [snapshot_id])
    scheme_id = loader.create_scheme(experiments_db, SplitScheme('at 1', label_cutoff=1))
    with pytest.raises(ValueError, match='no label history'):
        loader.materialise_split(experiments_db, snapshot_id, scheme_id)

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


# Scenario: card legality is per season. Read from the cards database's card_legality, which is filled from the official lists (#46).

def test_card_legality_is_per_season() -> None:
    legal = loader.load_legal_cards([30, 41])
    assert set(legal) == {30, 41}
    for cards in legal.values():
        assert {'Shock', 'Burst Lightning', 'Mountain'} <= cards
        assert not {'Lightning Bolt', 'Fireblast'} & cards

def test_cards_added_by_a_supplemental_rotation_are_legal() -> None:
    """Plasma Bolt came in season 38's supplemental rotation, which decksite's _legal_cards misses."""
    assert 'Plasma Bolt' in loader.load_legal_cards([38])[38]

def test_a_season_with_no_set_code_has_no_legal_cards_and_a_warning(caplog: pytest.LogCaptureFixture) -> None:
    assert loader.load_legal_cards([0]) == {0: frozenset()}
    assert 'season 0' in caplog.text


def test_the_command_line_snapshots_splits_and_summarises(labelled_seed: Container, experiments_db: Database, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(loader, 'experiments_db', lambda: experiments_db)
    for argv in (['snapshot', '--notes', 'test'], ['scheme', 'default'], ['split', '1', '1'], ['summary', '1', '1']):
        monkeypatch.setattr(sys, 'argv', ['loader', *argv])
        loader.main()
    out = capsys.readouterr().out.splitlines()
    assert out[:3] == ['Created snapshot 1', 'Created scheme 1', f'Split {len(labelled_seed.deck_ids)} decks']
    assert out[3] == out[6] and out[3].startswith('split {')  # split prints the same summary as summary does.
    assert sum(ast.literal_eval(out[3].removeprefix('split ')).values()) == len(labelled_seed.deck_ids)


def test_season_starts_come_from_the_site(labelled_seed: Container) -> None:
    start = db().value('SELECT start_date FROM season WHERE id = %s', [labelled_seed.season_id])
    assert loader.load_season_starts()[labelled_seed.season_id] == datetime.fromtimestamp(start, UTC)

def test_the_command_line_adds_history_and_makes_a_scheme_with_a_cutoff(labelled_seed: Container, experiments_db: Database, monkeypatch: pytest.MonkeyPatch,
                                                                        capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(loader, 'experiments_db', lambda: experiments_db)
    def run(*argv: str) -> None:
        monkeypatch.setattr(sys, 'argv', ['loader', *argv])
        loader.main()
    run('snapshot')
    experiments_db.execute('DELETE FROM label_change_snapshot WHERE snapshot_id = 1')
    run('history', '1')
    run('scheme', 'default')
    run('scheme', 'default at the seed season', '--like', '1', '--label-cutoff-season', str(labelled_seed.season_id))
    run('split', '1', '2')
    out = capsys.readouterr().out.splitlines()
    assert out[1:4] == ['Added 3 label history entries to snapshot 1', 'Created scheme 1', 'Created scheme 2']
    start = db().value('SELECT start_date FROM season WHERE id = %s', [labelled_seed.season_id])
    assert loader.load_scheme(experiments_db, 2) == SplitScheme('default at the seed season', label_cutoff=start)
    assert out[4] == f'Split {len(labelled_seed.deck_ids)} decks'

def test_splitting_from_the_command_line_prints_the_cutoff_counts(labelled_seed: Container, experiments_db: Database, monkeypatch: pytest.MonkeyPatch,
                                                                  capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(loader, 'experiments_db', lambda: experiments_db)
    snapshot_id = loader.create_snapshot(experiments_db)
    scheme_id = loader.create_scheme(experiments_db, SplitScheme('at 1', train_seasons=frozenset({labelled_seed.season_id}), held_out_percent=0, label_cutoff=1))
    monkeypatch.setattr(sys, 'argv', ['loader', 'split', str(snapshot_id), str(scheme_id)])
    loader.main()
    out = capsys.readouterr().out.splitlines()
    assert out[1] == "label cutoff {'same label': 1}"  # The validated deck: an automatic Aggro at 1, a person's Aggro at 2.
