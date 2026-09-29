from archetype_classifier.data_loading.dataset import ArchetypeRow, DeckCardRow, DeckRow, snapshot_decks
from archetype_classifier.data_loading.labels import LabelChange, Provenance

AGGRO = ArchetypeRow(1, 'Aggro', None)
RED_DECK_WINS = ArchetypeRow(2, 'Red Deck Wins', 1)
PRISONER = ArchetypeRow(3, 'Prisoner', 2)
ARCHETYPES = [AGGRO, RED_DECK_WINS, PRISONER]


def deck(deck_id: int, archetype_id: int, season_id: int = 30, source: str = 'League') -> DeckRow:
    return DeckRow(deck_id, season_id, source, archetype_id)

def burn(deck_id: int) -> list[DeckCardRow]:
    return [DeckCardRow(deck_id, 'Lightning Bolt', 4, False), DeckCardRow(deck_id, 'Mountain', 20, False)]


def test_a_corrected_guess_is_ground_truth_and_keeps_its_guess() -> None:
    history = [LabelChange(7, RED_DECK_WINS.id, by_person=False), LabelChange(7, PRISONER.id, by_person=True)]
    snapshot = snapshot_decks([deck(7, PRISONER.id)], history, burn(7), ARCHETYPES)
    assert snapshot.decks[7].ground_truth
    assert snapshot.decks[7].guess_archetype_id == RED_DECK_WINS.id

def test_an_unreviewed_guess_is_not_ground_truth() -> None:
    history = [LabelChange(8, RED_DECK_WINS.id, by_person=False)]
    snapshot = snapshot_decks([deck(8, RED_DECK_WINS.id)], history, burn(8), ARCHETYPES)
    assert not snapshot.decks[8].ground_truth

def test_a_label_changed_since_a_person_gave_it_is_not_ground_truth() -> None:
    history = [LabelChange(9, RED_DECK_WINS.id, by_person=False), LabelChange(9, PRISONER.id, by_person=True)]
    snapshot = snapshot_decks([deck(9, RED_DECK_WINS.id)], history, burn(9), ARCHETYPES)
    assert not snapshot.decks[9].ground_truth

def test_a_deck_with_no_label_history_is_not_ground_truth() -> None:
    snapshot = snapshot_decks([deck(10, PRISONER.id)], [], burn(10), ARCHETYPES)
    assert not snapshot.decks[10].ground_truth
    assert snapshot.decks[10].guess_archetype_id is None

def test_a_guess_a_person_kept_is_a_validated_guess_and_ground_truth() -> None:
    history = [LabelChange(11, PRISONER.id, by_person=False), LabelChange(11, PRISONER.id, by_person=True)]
    snapshot = snapshot_decks([deck(11, PRISONER.id)], history, burn(11), ARCHETYPES)
    assert snapshot.decks[11].provenance == Provenance.VALIDATED_GUESS
    assert snapshot.decks[11].ground_truth
    assert snapshot.decks[11].guess_archetype_id == PRISONER.id

def test_a_deck_a_person_labelled_without_a_guess_is_ground_truth_with_no_guess() -> None:
    snapshot = snapshot_decks([deck(12, PRISONER.id)], [LabelChange(12, PRISONER.id, by_person=True)], burn(12), ARCHETYPES)
    assert snapshot.decks[12].provenance == Provenance.PERSON_DIRECT
    assert snapshot.decks[12].ground_truth
    assert snapshot.decks[12].guess_archetype_id is None

def test_only_league_and_gatherling_decks_are_included() -> None:
    decks = [deck(20, PRISONER.id, source='League'), deck(21, PRISONER.id, source='Gatherling'), deck(22, PRISONER.id, source='MTG Goldfish'), deck(23, PRISONER.id, source='Tapped Out')]
    cards = [c for i in (20, 21, 22, 23) for c in burn(i)]
    snapshot = snapshot_decks(decks, [], cards, ARCHETYPES)
    assert set(snapshot.decks) == {20, 21}

def test_decks_labelled_unclassified_or_commander_are_left_out() -> None:
    unclassified, commander = ArchetypeRow(90, 'Unclassified', None), ArchetypeRow(91, 'Commander', None)
    decks = [deck(30, PRISONER.id), deck(31, unclassified.id), deck(32, commander.id)]
    cards = [c for i in (30, 31, 32) for c in burn(i)]
    snapshot = snapshot_decks(decks, [], cards, [*ARCHETYPES, unclassified, commander])
    assert set(snapshot.decks) == {30}

def test_decks_with_no_cards_are_left_out() -> None:
    sideboard_only = [DeckCardRow(42, 'Smash to Smithereens', 3, True)]
    snapshot = snapshot_decks([deck(40, PRISONER.id), deck(41, PRISONER.id), deck(42, PRISONER.id)], [], burn(40) + sideboard_only, ARCHETYPES)
    assert set(snapshot.decks) == {40, 42}
