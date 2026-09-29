from archetype_classifier.data_loading.dataset import ArchetypeRow, DeckCardRow, DeckRow, snapshot_decks
from archetype_classifier.data_loading.labels import LabelChange

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
