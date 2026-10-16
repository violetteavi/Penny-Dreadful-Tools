from collections import Counter
from datetime import UTC, datetime

import pytest

from archetype_classifier.data_loading.dataset import ArchetypeRow, DeckCardRow, DeckRow, DeckSplit, TwinOverlap, snapshot_decks, split_decks, twin_overlaps
from archetype_classifier.data_loading.labels import LabelChange, LabelFacts, LabelStatus
from archetype_classifier.data_loading.splits import ExclusionReason, Split, SplitScheme

AGGRO = ArchetypeRow(1, 'Aggro', None)
RED_DECK_WINS = ArchetypeRow(2, 'Red Deck Wins', 1)
PRISONER = ArchetypeRow(3, 'Prisoner', 2)
ARCHETYPES = [AGGRO, RED_DECK_WINS, PRISONER]
EPOCH = datetime(2020, 1, 1, tzinfo=UTC)  # Order is all these tests need.


MARCH_2 = datetime(2024, 3, 2, tzinfo=UTC)
MARCH_5 = datetime(2024, 3, 5, tzinfo=UTC)

def deck(deck_id: int, archetype_id: int | None, season_id: int = 30, source: str = 'League', reviewed: bool = True) -> DeckRow:
    return DeckRow(deck_id, season_id, source, archetype_id, reviewed)

def burn(deck_id: int) -> list[DeckCardRow]:
    """A 60-card maindeck legal in seasons 20-43, with a sideboard card that never counts towards the maindeck."""
    return [DeckCardRow(deck_id, 'Shock', 4, False), DeckCardRow(deck_id, 'Mountain', 56, False), DeckCardRow(deck_id, 'Smash to Smithereens', 2, True)]

def test_the_snapshot_freezes_every_deck_with_its_facts() -> None:
    history = [LabelChange(1, PRISONER.id, by_person=True, changed_at=MARCH_2), LabelChange(1, RED_DECK_WINS.id, by_person=False, changed_at=MARCH_5)]
    decks = [deck(1, PRISONER.id), deck(2, PRISONER.id, source='Tapped Out', reviewed=False), deck(3, None), deck(4, PRISONER.id)]
    snapshot = snapshot_decks(decks, history, burn(1) + burn(2) + burn(3), ARCHETYPES)
    assert set(snapshot.decks) == {1, 2, 3, 4}
    first = snapshot.decks[1]
    assert (first.season_id, first.source, first.reviewed, first.maindeck_cards, first.site_archetype_id) == (30, 'League', True, 60, PRISONER.id)
    assert first.labels == LabelFacts(PRISONER.id, MARCH_2, RED_DECK_WINS.id, MARCH_5)
    assert (snapshot.decks[2].source, snapshot.decks[2].reviewed) == ('Tapped Out', False)
    assert snapshot.decks[3].site_archetype_id is None
    assert (snapshot.decks[4].maindeck_hash, snapshot.decks[4].maindeck_cards) == (None, 0)  # No cards at all.

def test_identical_maindecks_share_a_hash_whatever_their_sideboards() -> None:
    first = burn(50) + [DeckCardRow(50, 'Smash to Smithereens', 1, True)]
    same_maindeck_other_order = list(reversed(burn(51))) + [DeckCardRow(51, 'Island', 2, True)]
    different_maindeck = [DeckCardRow(52, 'Shock', 3, False), DeckCardRow(52, 'Mountain', 57, False)]
    decks = [deck(50, PRISONER.id), deck(51, PRISONER.id), deck(52, PRISONER.id)]
    snapshot = snapshot_decks(decks, [], first + same_maindeck_other_order + different_maindeck, ARCHETYPES)
    assert snapshot.decks[50].maindeck_hash == snapshot.decks[51].maindeck_hash
    assert snapshot.decks[50].maindeck_hash != snapshot.decks[52].maindeck_hash

def test_the_snapshot_freezes_the_archetype_tree_with_depths() -> None:
    snapshot = snapshot_decks([], [], [], ARCHETYPES)
    assert [(a.name, a.parent_id, a.depth) for a in snapshot.archetypes.values()] == [('Aggro', None, 0), ('Red Deck Wins', AGGRO.id, 1), ('Prisoner', RED_DECK_WINS.id, 2)]







# Scenario: an excluded deck changes nothing else (Scenarios.md, "Splitting decks").

def red_deck(deck_id: int, cards: dict[str, int]) -> list[DeckCardRow]:
    return [DeckCardRow(deck_id, card, n, False) for card, n in cards.items()]

INVARIANT_CARDS = red_deck(1, {'Shock': 4, 'Mountain': 56}) + red_deck(2, {'Burst Lightning': 4, 'Mountain': 56}) + red_deck(3, {'Shock': 4, 'Burst Lightning': 4, 'Mountain': 52})
INVARIANT_HISTORY = [LabelChange(1, RED_DECK_WINS.id, by_person=True, changed_at=MARCH_2), LabelChange(3, RED_DECK_WINS.id, by_person=True, changed_at=MARCH_2)]
NOTHING_HELD_OUT = SplitScheme('typical, nothing held out', held_out_percent=0)  # So A is TRAIN whatever its maindeck hash.

def test_an_excluded_deck_changes_nothing_else() -> None:
    a, b, c = deck(1, RED_DECK_WINS.id, season_id=30), deck(2, None, season_id=30), deck(3, RED_DECK_WINS.id, season_id=41)
    with_b = split_decks(snapshot_decks([a, b, c], INVARIANT_HISTORY, INVARIANT_CARDS, ARCHETYPES), INVARIANT_CARDS, NOTHING_HELD_OUT)
    without_b = split_decks(snapshot_decks([a, c], INVARIANT_HISTORY, INVARIANT_CARDS, ARCHETYPES), INVARIANT_CARDS, NOTHING_HELD_OUT)

    assert (with_b.decks[1].split, with_b.decks[1].label_status) == (Split.TRAIN, LabelStatus.VERIFIED)
    assert (with_b.decks[2].split, with_b.decks[2].reason, with_b.decks[2].label_status) == (Split.EXCLUDED, ExclusionReason.STATUS_NOT_TRAINED_ON, LabelStatus.UNLABELLED)
    assert (with_b.decks[3].split, with_b.decks[3].label_id) == (Split.TEST, RED_DECK_WINS.id)
    assert with_b.decks[3].unseen_maindeck_copies == 4  # The four Burst Lightning: B has them, but B isn't a training deck.
    assert {i: s for i, s in with_b.decks.items() if i != 2} == without_b.decks
    assert with_b.report.by_reason - without_b.report.by_reason == Counter({ExclusionReason.STATUS_NOT_TRAINED_ON: 1})

def test_an_unlabelled_twin_held_out_by_its_deck_id_changes_nothing_for_its_training_twin() -> None:
    twins = SplitScheme('twins', allow_held_out_twins=True)  # Deck id 1 falls outside the held-out 10%, deck id 4 inside it.
    a, twin = deck(1, RED_DECK_WINS.id, season_id=30), deck(4, None, season_id=30)
    cards = red_deck(1, {'Shock': 4, 'Mountain': 56}) + red_deck(4, {'Shock': 4, 'Mountain': 56})
    with_twin = split_decks(snapshot_decks([a, twin], INVARIANT_HISTORY, cards, ARCHETYPES), cards, twins)
    without_twin = split_decks(snapshot_decks([a], INVARIANT_HISTORY, cards, ARCHETYPES), cards, twins)
    assert (with_twin.decks[4].split, with_twin.decks[4].reason) == (Split.EXCLUDED, ExclusionReason.STATUS_NOT_EVALUATED)
    assert with_twin.decks[1].split == Split.TRAIN
    assert with_twin.decks[1] == without_twin.decks[1]


# Scenario: a card is unseen unless a training maindeck has it.

def test_a_card_is_unseen_unless_a_training_maindeck_has_it() -> None:
    history = [LabelChange(i, RED_DECK_WINS.id, by_person=True, changed_at=MARCH_2) for i in (1, 2, 3)]
    training = red_deck(1, {'Shock': 4, 'Mountain': 56}) + [DeckCardRow(1, 'Smash to Smithereens', 2, True)]
    validation = red_deck(2, {'Island': 4, 'Mountain': 56})
    test = red_deck(3, {'Shock': 4, 'Smash to Smithereens': 4, 'Island': 4, 'Mountain': 48})
    cards = training + validation + test
    decks = [deck(1, RED_DECK_WINS.id, season_id=30), deck(2, RED_DECK_WINS.id, season_id=39), deck(3, RED_DECK_WINS.id, season_id=41)]
    splits = split_decks(snapshot_decks(decks, history, cards, ARCHETYPES), cards, NOTHING_HELD_OUT)
    assert [splits.decks[i].split for i in (1, 2, 3)] == [Split.TRAIN, Split.VALIDATION, Split.TEST]
    assert splits.decks[3].unseen_maindeck_copies == 8  # Smash to Smithereens was only in a training sideboard; Island only in a validation deck.
    assert splits.decks[2].unseen_maindeck_copies == 4


# Scenario: a maindeck in both TRAIN and HELD_OUT is reported, not fatal.

def test_a_maindeck_in_both_train_and_held_out_is_reported_unless_twins_are_allowed() -> None:
    def deck_split(deck_id: int, split: Split) -> DeckSplit:
        return DeckSplit(deck_id, split, None, LabelStatus.VERIFIED, RED_DECK_WINS.id, 0)
    splits = {1: deck_split(1, Split.TRAIN), 2: deck_split(2, Split.HELD_OUT), 3: deck_split(3, Split.HELD_OUT)}  # Built by hand: the default can't produce this.
    hashes = {1: 'a' * 40, 2: 'a' * 40, 3: 'b' * 40}
    assert twin_overlaps(splits, hashes, SplitScheme('typical')) == [TwinOverlap('a' * 40, frozenset({1}), frozenset({2}))]
    assert twin_overlaps(splits, hashes, SplitScheme('twins', allow_held_out_twins=True)) == []


# Scenario: a large maindeck loads in full (the snapshot half; loading its contents is tested with the loader).

def test_a_112_card_maindeck_is_frozen_in_full_and_not_excluded() -> None:
    life_is_ez = red_deck(217677, {'Shock': 4, 'Mountain': 108}) + [DeckCardRow(217677, 'Smash to Smithereens', 15, True)]  # Both legal in season 29.
    history = [LabelChange(217677, RED_DECK_WINS.id, by_person=True, changed_at=MARCH_2)]
    snapshot = snapshot_decks([deck(217677, RED_DECK_WINS.id, season_id=29)], history, life_is_ez, ARCHETYPES)
    assert snapshot.decks[217677].maindeck_cards == 112
    assert snapshot.decks[217677].maindeck_hash != snapshot_decks([deck(1, RED_DECK_WINS.id)], [], burn(1), ARCHETYPES).decks[1].maindeck_hash
    assert split_decks(snapshot, life_is_ez, NOTHING_HELD_OUT).decks[217677].split == Split.TRAIN


# Scenario: a training deck relabelled after the cutoff trains on its label at the cutoff (Scenarios.md, "Labels at a cutoff").

FLARE_DECK_WINS = ArchetypeRow(4, 'Flare Deck Wins', 2)
EQUIPMENT_AGGRO = ArchetypeRow(5, 'Equipment Aggro', 1)
BURN = ArchetypeRow(6, 'Burn', 1)
UNCLASSIFIED = ArchetypeRow(7, 'Unclassified', None)
WILDFIRE = ArchetypeRow(8, 'Wildfire', None)
THRYX_WILDFIRE = ArchetypeRow(9, 'Thryx-Wildfire', 8)
CUTOFF_ARCHETYPES = [*ARCHETYPES, FLARE_DECK_WINS, EQUIPMENT_AGGRO, BURN, UNCLASSIFIED, WILDFIRE, THRYX_WILDFIRE]
CUTOFF = datetime(2025, 10, 3, 7, tzinfo=UTC)  # The start of season 39.
BEFORE = datetime(2025, 6, 1, tzinfo=UTC)
AFTER = datetime(2026, 4, 8, tzinfo=UTC)
AT_SEASON_39 = SplitScheme('typical at season 39, nothing held out', held_out_percent=0, label_cutoff=int(CUTOFF.timestamp()))

def person(deck_id: int, archetype: ArchetypeRow, at: datetime) -> LabelChange:
    return LabelChange(deck_id, archetype.id, by_person=True, changed_at=at)

def automatic(deck_id: int, archetype: ArchetypeRow, at: datetime) -> LabelChange:
    return LabelChange(deck_id, archetype.id, by_person=False, changed_at=at)

CUTOFF_HISTORY = [
    person(1, RED_DECK_WINS, BEFORE), person(1, FLARE_DECK_WINS, AFTER),  # A
    automatic(2, RED_DECK_WINS, BEFORE), person(2, EQUIPMENT_AGGRO, AFTER),  # B
    person(3, EQUIPMENT_AGGRO, AFTER),  # C
    person(4, UNCLASSIFIED, BEFORE), person(4, BURN, AFTER),  # D
    person(5, BURN, BEFORE), automatic(5, RED_DECK_WINS, AFTER),  # E: the site refused the guess.
    person(6, BURN, CUTOFF), person(6, RED_DECK_WINS, AFTER),  # F
    person(7, WILDFIRE, BEFORE),  # G: later moved to Thryx-Wildfire without history.
]
CUTOFF_DECKS = [deck(1, FLARE_DECK_WINS.id), deck(2, EQUIPMENT_AGGRO.id), deck(3, EQUIPMENT_AGGRO.id), deck(4, BURN.id), deck(5, BURN.id), deck(6, RED_DECK_WINS.id),
                deck(7, THRYX_WILDFIRE.id)]
CUTOFF_CARDS = [c for i in range(1, 8) for c in burn(i)]

def by_deck(history: list[LabelChange]) -> dict[int, list[LabelChange]]:
    grouped: dict[int, list[LabelChange]] = {}
    for c in history:
        grouped.setdefault(c.deck_id, []).append(c)
    return grouped

def test_training_decks_relabelled_after_the_cutoff_train_on_their_label_at_the_cutoff() -> None:
    snapshot = snapshot_decks(CUTOFF_DECKS, CUTOFF_HISTORY, CUTOFF_CARDS, CUTOFF_ARCHETYPES)
    splits = split_decks(snapshot, CUTOFF_CARDS, AT_SEASON_39, by_deck(CUTOFF_HISTORY))
    trained_on, not_trained_on = (Split.TRAIN, None), (Split.EXCLUDED, ExclusionReason.STATUS_NOT_TRAINED_ON)
    expected = {
        1: (*trained_on, LabelStatus.VERIFIED, RED_DECK_WINS.id),
        2: (*not_trained_on, LabelStatus.UNVERIFIED, RED_DECK_WINS.id),
        3: (*not_trained_on, LabelStatus.UNLABELLED, None),
        4: (*not_trained_on, LabelStatus.OUT_OF_SCOPE, None),
        5: (*trained_on, LabelStatus.VERIFIED, BURN.id),
        6: (*trained_on, LabelStatus.VERIFIED, BURN.id),
        7: (*not_trained_on, LabelStatus.UNVERIFIED, THRYX_WILDFIRE.id),  # The label rule, exactly as without a cutoff.
    }
    assert {i: (s.split, s.reason, s.label_status, s.label_id) for i, s in splits.decks.items()} == expected
    assert splits.report.cutoff_labels == Counter({'same label': 1, 'different label': 3, 'no label': 1, 'out of scope': 1})


# Scenario: scored decks keep today's label.

def a_history(deck_id: int) -> list[LabelChange]:
    return [person(deck_id, RED_DECK_WINS, BEFORE), person(deck_id, FLARE_DECK_WINS, AFTER)]

def test_held_out_validation_and_test_decks_keep_todays_label_under_a_cutoff() -> None:
    held_out_scheme = SplitScheme('typical at season 39, everything held out', held_out_percent=100, label_cutoff=AT_SEASON_39.label_cutoff)
    decks = [deck(11, FLARE_DECK_WINS.id, season_id=30), deck(12, FLARE_DECK_WINS.id, season_id=39), deck(13, FLARE_DECK_WINS.id, season_id=41)]
    history = a_history(11) + a_history(12) + a_history(13)
    cards = burn(11) + burn(12) + burn(13)
    splits = split_decks(snapshot_decks(decks, history, cards, CUTOFF_ARCHETYPES), cards, held_out_scheme, by_deck(history))
    assert [(splits.decks[i].split, splits.decks[i].label_status, splits.decks[i].label_id) for i in (11, 12, 13)] == [
        (Split.HELD_OUT, LabelStatus.VERIFIED, FLARE_DECK_WINS.id), (Split.VALIDATION, LabelStatus.VERIFIED, FLARE_DECK_WINS.id), (Split.TEST, LabelStatus.VERIFIED, FLARE_DECK_WINS.id)]
    assert splits.report.cutoff_labels == Counter()

def test_a_deck_held_out_by_its_deck_id_keeps_todays_label() -> None:
    twins = SplitScheme('twins at season 39', allow_held_out_twins=True, label_cutoff=AT_SEASON_39.label_cutoff)  # Deck id 4 is held out; its maindeck alone wouldn't be.
    splits = split_decks(snapshot_decks([deck(4, FLARE_DECK_WINS.id)], a_history(4), burn(4), CUTOFF_ARCHETYPES), burn(4), twins, by_deck(a_history(4)))
    assert (splits.decks[4].split, splits.decks[4].label_id) == (Split.HELD_OUT, FLARE_DECK_WINS.id)

def test_an_earlier_automatic_label_is_trained_on_by_a_scheme_that_trains_on_unverified_decks() -> None:
    widened = SplitScheme('baseline at season 39', held_out_percent=0, train_statuses=frozenset({LabelStatus.VERIFIED, LabelStatus.UNVERIFIED}),
                          label_cutoff=AT_SEASON_39.label_cutoff)
    snapshot = snapshot_decks(CUTOFF_DECKS, CUTOFF_HISTORY, CUTOFF_CARDS, CUTOFF_ARCHETYPES)
    b = split_decks(snapshot, CUTOFF_CARDS, widened, by_deck(CUTOFF_HISTORY)).decks[2]
    assert (b.split, b.label_status, b.label_id) == (Split.TRAIN, LabelStatus.UNVERIFIED, RED_DECK_WINS.id)


# Scenario: adding history to a snapshot refuses a changed dump (the splitting half).

def test_a_scheme_with_a_cutoff_refuses_to_split_without_the_label_history() -> None:
    snapshot = snapshot_decks(CUTOFF_DECKS, CUTOFF_HISTORY, CUTOFF_CARDS, CUTOFF_ARCHETYPES)
    with pytest.raises(ValueError, match='label history'):
        split_decks(snapshot, CUTOFF_CARDS, AT_SEASON_39)
