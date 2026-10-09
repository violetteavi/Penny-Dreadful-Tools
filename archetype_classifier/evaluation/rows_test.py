import logging

import pytest

from archetype_classifier.data_loading.labels import LabelFacts, LabelStatus
from archetype_classifier.data_loading.slices import Snapshot, SnapshotDeck, build_deck_set
from archetype_classifier.data_loading.splits import Split, SplitScheme
from archetype_classifier.evaluation.rows import ROWS_VERSION, build_rows

RED_DECK_WINS = 16
MAINDECK_A, MAINDECK_B = 'a' * 40, 'b' * 40
TYPICAL = SplitScheme('typical')

# The decks of "Rows of the results table" (Scenarios.md): deck id -> split, unseen maindeck copies, maindeck.
DECKS = {101: (Split.TRAIN, 0, MAINDECK_A), 102: (Split.TRAIN, 0, MAINDECK_B), 301: (Split.HELD_OUT, 0, None), 302: (Split.HELD_OUT, 3, None),
         201: (Split.VALIDATION, 0, MAINDECK_A), 202: (Split.VALIDATION, 3, None), 401: (Split.TEST, 0, MAINDECK_B), 402: (Split.TEST, 2, None),
         403: (Split.TEST, 7, None), 404: (Split.TEST, 15, None)}


def snapshot_deck(deck_id: int, split: Split, unseen: int, maindeck: str | None, status: LabelStatus = LabelStatus.VERIFIED) -> SnapshotDeck:
    return SnapshotDeck(deck_id=deck_id, season_id=30, source='League', maindeck_hash=maindeck or f'{deck_id:040x}', reviewed=True, split=split, exclusion_reason=None,
                        label_status=status, label_id=RED_DECK_WINS, unseen_maindeck_copies=unseen, labels=LabelFacts(None, None, None, None), site_archetype_id=RED_DECK_WINS)

def snapshot(decks: dict[int, SnapshotDeck], scheme: SplitScheme = TYPICAL) -> Snapshot:
    return Snapshot(decks, {}, scheme)

SNAPSHOT = snapshot({i: snapshot_deck(i, *d) for i, d in DECKS.items()})

def rows(scored: set[Split], from_snapshot: Snapshot = SNAPSHOT) -> dict[str, frozenset[int]]:
    deck_set = build_deck_set(from_snapshot, frozenset(scored), include_test=Split.TEST in scored)
    return {r.name: r.deck_ids for r in build_rows(deck_set, build_deck_set(from_snapshot, frozenset({Split.TRAIN})), from_snapshot.scheme)}


# Scenario: scoring held-out and validation decks gives their rows.

def test_scoring_held_out_and_validation_decks_gives_their_rows() -> None:
    assert rows({Split.HELD_OUT, Split.VALIDATION}) == {
        'held-out, no unseen cards': frozenset({301}),
        'held-out, unseen cards': frozenset({302}),
        'validation': frozenset({201, 202}),
        'validation, no unseen cards': frozenset({201}),
        'validation, unseen cards': frozenset({202}),
        'validation, new maindeck': frozenset({202}),
        'validation, repeated maindeck': frozenset({201}),
    }


# Scenario: test rows split by unseen copies (the gate and the logged look are tested with scoring).

def test_test_rows_split_by_unseen_copies_and_by_repeated_maindeck() -> None:
    assert rows({Split.TEST}) == {
        'test, overall': frozenset({401, 402, 403, 404}),
        'test, 0 unseen copies': frozenset({401}),
        'test, 1–4 unseen copies': frozenset({402}),
        'test, 5–12 unseen copies': frozenset({403}),
        'test, 13+ unseen copies': frozenset({404}),
        'test, new maindeck': frozenset({402, 403, 404}),
        'test, repeated maindeck': frozenset({401}),
    }


# Scenario: scoring the training decks gives one in-sample row.

def test_scoring_the_training_decks_gives_one_in_sample_row() -> None:
    assert rows({Split.TRAIN}) == {'train, in-sample': frozenset({101, 102})}


# Scenario: unverified labels get their own row.

def test_unverified_labels_get_their_own_row() -> None:
    evaluates_unverified = SplitScheme('unverified too', eval_statuses=frozenset({LabelStatus.VERIFIED, LabelStatus.UNVERIFIED}))
    decks = {**SNAPSHOT.decks, 303: snapshot_deck(303, Split.HELD_OUT, 0, None, LabelStatus.UNVERIFIED)}
    assert rows({Split.HELD_OUT}, snapshot(decks, evaluates_unverified)) == {
        'held-out, no unseen cards': frozenset({301}),
        'held-out, unseen cards': frozenset({302}),
        'held-out, unverified labels': frozenset({303}),
    }


# Scenario: a row with no decks is left out.

def test_a_row_with_no_decks_is_left_out(caplog: pytest.LogCaptureFixture) -> None:
    no_unseen = snapshot({**SNAPSHOT.decks, 302: snapshot_deck(302, Split.HELD_OUT, 0, None)})
    with caplog.at_level(logging.INFO):
        assert rows({Split.HELD_OUT}, no_unseen) == {'held-out, no unseen cards': frozenset({301, 302})}
    assert "Row 'held-out, unseen cards' has no decks, so it's left out" in caplog.text


# With twins allowed, held-out decks can repeat a training maindeck, so they get maindeck rows too.

def test_with_twins_allowed_held_out_decks_get_maindeck_rows() -> None:
    twins = SplitScheme('twins', allow_held_out_twins=True)
    decks = {**SNAPSHOT.decks, 301: snapshot_deck(301, Split.HELD_OUT, 0, MAINDECK_A)}  # Repeats deck 101.
    found = rows({Split.HELD_OUT}, snapshot(decks, twins))
    assert (found['held-out, new maindeck'], found['held-out, repeated maindeck']) == (frozenset({302}), frozenset({301}))


# Scenario: rows are versioned.

def test_rows_are_versioned() -> None:
    assert ROWS_VERSION == 2
