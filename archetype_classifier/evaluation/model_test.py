from archetype_classifier.data_loading.dataset import CardCount, DeckContents
from archetype_classifier.data_loading.labels import LabelFacts, LabelStatus
from archetype_classifier.data_loading.slices import Snapshot, SnapshotDeck, build_deck_set
from archetype_classifier.data_loading.splits import Split, SplitScheme
from archetype_classifier.evaluation.model import LabelledDeck, PredictDeck, build_labelled_decks, build_predict_decks

RED_DECK_WINS = 2
AZORIUS_CONTROL = 3

# The decks of the "Model inputs" scenarios (Scenarios.md). Every card is legal in seasons 30 and 39.
CONTENTS = {
    1: DeckContents((CardCount('Mountain', 56), CardCount('Shock', 4)), (CardCount('Smash to Smithereens', 2),)),
    2: DeckContents((CardCount('Essence Scatter', 4), CardCount('Island', 56)), (CardCount('Negate', 2),)),
    3: DeckContents((CardCount('Mountain', 56), CardCount('Shock', 4)), ()),
    4: DeckContents((CardCount('Mountain', 56), CardCount('Shock', 4)), ()),
}


def snapshot_deck(deck_id: int, season_id: int, split: Split, status: LabelStatus, label_id: int | None, reviewed: bool = True) -> SnapshotDeck:
    return SnapshotDeck(deck_id=deck_id, season_id=season_id, source='League', maindeck_hash=f'{deck_id:040x}', reviewed=reviewed, split=split, exclusion_reason=None,
                        label_status=status, label_id=label_id, unseen_maindeck_copies=0, labels=LabelFacts(None, None, None, None), site_archetype_id=label_id)

def snapshot(*decks: SnapshotDeck) -> Snapshot:
    return Snapshot({d.deck_id: d for d in decks}, {}, SplitScheme('typical'))

VALIDATION_DECKS = snapshot(snapshot_deck(1, 39, Split.VALIDATION, LabelStatus.VERIFIED, RED_DECK_WINS), snapshot_deck(2, 39, Split.VALIDATION, LabelStatus.VERIFIED, AZORIUS_CONTROL))


# Scenario: labelled and prediction decks come from the same deck set.

def test_labelled_and_prediction_decks_come_from_the_same_deck_set() -> None:
    deck_set = build_deck_set(VALIDATION_DECKS, frozenset({Split.VALIDATION}))
    deck_1 = PredictDeck(1, 'League', CONTENTS[1].maindeck, CONTENTS[1].sideboard)
    deck_2 = PredictDeck(2, 'League', CONTENTS[2].maindeck, CONTENTS[2].sideboard)
    assert build_labelled_decks(deck_set, CONTENTS) == [LabelledDeck(deck_1, RED_DECK_WINS, f'{1:040x}'), LabelledDeck(deck_2, AZORIUS_CONTROL, f'{2:040x}')]
    assert build_predict_decks(deck_set, CONTENTS) == [deck_1, deck_2]
    assert sum(c.n for c in deck_1.maindeck) == 60 and sum(c.n for c in deck_1.sideboard) == 2
