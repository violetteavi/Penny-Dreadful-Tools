from collections import Counter
from datetime import UTC, datetime

from archetype_classifier.data_loading.dataset import ArchetypeRow, DeckCardRow, DeckRow, snapshot_decks, split_decks
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
