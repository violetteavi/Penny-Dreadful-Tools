from datetime import UTC, datetime

from archetype_classifier.data_loading.dataset import ArchetypeRow, DeckCardRow, DeckRow, snapshot_decks, split_decks
from archetype_classifier.data_loading.labels import LabelChange, LabelFacts
from archetype_classifier.data_loading.splits import Split, SplitScheme

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

def test_seasons_decide_the_split_and_the_reserved_season_is_left_out() -> None:
    seasons = {60: 38, 61: 39, 62: 40, 63: 42, 64: 43}
    decks = [deck(i, PRISONER.id, season_id=s) for i, s in seasons.items()]
    cards = [c for i in seasons for c in burn(i)]
    snapshot = snapshot_decks(decks, [], cards, ARCHETYPES)
    splits = split_decks(snapshot, cards, SplitScheme('default'))
    assert {i: s.split for i, s in splits.items()} == {60: Split.TRAIN, 61: Split.VALIDATION, 62: Split.TEST, 63: Split.TEST}

def distinct_training_decks(count: int) -> tuple[list[DeckRow], list[DeckCardRow]]:
    """`count` distinct maindecks, each with a twin that has the same maindeck and a different sideboard."""
    decks, cards = [], []
    for i in range(count):
        original, twin = 1000 + 2 * i, 1001 + 2 * i
        decks += [deck(original, PRISONER.id, season_id=20), deck(twin, PRISONER.id, season_id=30)]
        cards += [DeckCardRow(original, f'Card {i}', 4, False), DeckCardRow(original, 'Pyroblast', 1, True)]
        cards += [DeckCardRow(twin, f'Card {i}', 4, False), DeckCardRow(twin, 'Smash to Smithereens', 2, True)]
    return decks, cards

def test_about_ten_percent_of_training_decklists_are_held_out_and_twins_stay_together() -> None:
    decks, cards = distinct_training_decks(2000)
    splits = split_decks(snapshot_decks(decks, [], cards, ARCHETYPES), cards, SplitScheme('default'))
    originals = [splits[1000 + 2 * i].split for i in range(2000)]
    twins = [splits[1001 + 2 * i].split for i in range(2000)]
    assert originals == twins
    assert set(originals) == {Split.TRAIN, Split.HELD_OUT}
    assert 8 <= 100 * originals.count(Split.HELD_OUT) / 2000 <= 12

def test_a_different_salt_gives_a_different_held_out_set() -> None:
    decks, cards = distinct_training_decks(2000)
    snapshot = snapshot_decks(decks, [], cards, ARCHETYPES)
    first = {i for i, s in split_decks(snapshot, cards, SplitScheme('default')).items() if s.split == Split.HELD_OUT}
    second = {i for i, s in split_decks(snapshot, cards, SplitScheme('resampled', salt='2')).items() if s.split == Split.HELD_OUT}
    assert first != second
    assert 0.8 <= len(second) / len(first) <= 1.25

def test_unseen_copies_count_maindeck_cards_missing_from_training_maindecks() -> None:
    training = [DeckCardRow(70, 'Lightning Bolt', 4, False), DeckCardRow(70, 'Mountain', 20, False), DeckCardRow(70, 'Pyroblast', 2, True)]
    new_season = [DeckCardRow(71, 'Lightning Bolt', 4, False), DeckCardRow(71, 'Pyroblast', 3, False), DeckCardRow(71, 'Grounded for Life', 2, False),
                  DeckCardRow(71, 'Mountain', 17, False), DeckCardRow(71, "Ajani's Response", 1, True)]
    cards = training + new_season
    snapshot = snapshot_decks([deck(70, PRISONER.id, season_id=20), deck(71, PRISONER.id, season_id=40)], [], cards, ARCHETYPES)
    splits = split_decks(snapshot, cards, SplitScheme('no held-out', held_out_percent=0))
    assert splits[70].unseen_maindeck_copies == 0
    assert splits[71].unseen_maindeck_copies == 5  # Pyroblast was only in a training sideboard; the sideboard's Ajani's Response doesn't count.

def test_a_card_only_in_held_out_decks_is_unseen_for_them() -> None:
    decks, cards = distinct_training_decks(500)
    splits = split_decks(snapshot_decks(decks, [], cards, ARCHETYPES), cards, SplitScheme('default'))
    assert {s.unseen_maindeck_copies for s in splits.values() if s.split == Split.HELD_OUT} == {4}
    assert {s.unseen_maindeck_copies for s in splits.values() if s.split == Split.TRAIN} == {0}






