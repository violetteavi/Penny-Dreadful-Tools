from archetype_classifier.data_loading.labels import LabelFacts, LabelStatus
from archetype_classifier.data_loading.slices import Snapshot, SnapshotDeck, build_deck_set
from archetype_classifier.data_loading.splits import Split, SplitScheme
from archetype_classifier.evaluation.rows import build_rows

RED_DECK_WINS = 16
MAINDECK_A, MAINDECK_B = 'a' * 40, 'b' * 40
TYPICAL = SplitScheme('typical')

# The decks of "Rows of the results table" (Scenarios.md): deck id -> split, unseen maindeck copies, maindeck.
DECKS = {101: (Split.TRAIN, 0, MAINDECK_A), 102: (Split.TRAIN, 0, MAINDECK_B), 301: (Split.HELD_OUT, 0, None), 302: (Split.HELD_OUT, 3, None),
         201: (Split.VALIDATION, 0, MAINDECK_A), 202: (Split.VALIDATION, 0, None), 401: (Split.TEST, 0, MAINDECK_B), 402: (Split.TEST, 2, None),
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
