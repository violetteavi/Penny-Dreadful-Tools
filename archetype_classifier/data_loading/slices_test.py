import pytest

from archetype_classifier.data_loading.labels import LabelFacts, LabelStatus
from archetype_classifier.data_loading.slices import Snapshot, SnapshotDeck, build_deck_set
from archetype_classifier.data_loading.splits import ExclusionReason, Split, SplitScheme

RED_DECK_WINS = 2


def snapshot_deck(deck_id: int, split: Split) -> SnapshotDeck:
    reason = ExclusionReason.STATUS_NOT_TRAINED_ON if split == Split.EXCLUDED else None
    return SnapshotDeck(deck_id=deck_id, season_id=30, source='League', maindeck_hash=f'{deck_id:040x}', reviewed=True, split=split, exclusion_reason=reason,
                        label_status=LabelStatus.VERIFIED, label_id=RED_DECK_WINS, unseen_maindeck_copies=0,
                        labels=LabelFacts(RED_DECK_WINS, None, None, None), site_archetype_id=RED_DECK_WINS)

# Scenario: a deck set holds exactly the decks in its splits (Scenarios.md, "Splitting decks"). The splits are given, so no scheme is involved.
SPLITS = {1: Split.TRAIN, 2: Split.TRAIN, 3: Split.TRAIN, 4: Split.HELD_OUT, 5: Split.HELD_OUT, 6: Split.VALIDATION, 7: Split.TEST, 8: Split.EXCLUDED, 9: Split.EXCLUDED}
SNAPSHOT = Snapshot({i: snapshot_deck(i, s) for i, s in SPLITS.items()}, {}, SplitScheme('typical'))


def test_a_deck_set_holds_exactly_the_decks_in_its_splits() -> None:
    assert set(build_deck_set(SNAPSHOT, frozenset({Split.TRAIN})).decks) == {1, 2, 3}
    held_out_and_validation = build_deck_set(SNAPSHOT, frozenset({Split.HELD_OUT, Split.VALIDATION}))
    assert set(held_out_and_validation.decks) == {4, 5, 6}
    assert held_out_and_validation.splits == frozenset({Split.HELD_OUT, Split.VALIDATION})

def test_excluded_decks_cant_be_picked_and_test_decks_need_the_gate() -> None:
    with pytest.raises(ValueError, match='EXCLUDED'):
        build_deck_set(SNAPSHOT, frozenset({Split.EXCLUDED}))
    with pytest.raises(ValueError, match='include_test'):
        build_deck_set(SNAPSHOT, frozenset({Split.VALIDATION, Split.TEST}))
    assert set(build_deck_set(SNAPSHOT, frozenset({Split.TEST}), include_test=True).decks) == {7}

def test_a_deck_sets_fingerprint_depends_only_on_its_decks() -> None:
    forwards = build_deck_set(SNAPSHOT, frozenset({Split.TRAIN}))
    backwards = build_deck_set(Snapshot(dict(reversed(SNAPSHOT.decks.items())), {}, SNAPSHOT.scheme), frozenset({Split.TRAIN}))
    one_more = build_deck_set(SNAPSHOT, frozenset({Split.TRAIN, Split.VALIDATION}))
    assert forwards.deck_ids_hash == backwards.deck_ids_hash
    assert forwards.deck_ids_hash != one_more.deck_ids_hash


# Scenario: a deck the snapshot doesn't contain is excluded.

def test_a_deck_the_snapshot_doesnt_contain_is_excluded() -> None:
    assert SNAPSHOT.split_of(1) == (Split.TRAIN, None)
    assert SNAPSHOT.split_of(284191) == (Split.EXCLUDED, ExclusionReason.NOT_IN_SNAPSHOT)
