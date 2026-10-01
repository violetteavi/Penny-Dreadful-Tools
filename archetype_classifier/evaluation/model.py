"""What a model sees. A deck set picks the decks; these functions only change their shape, attaching each deck's cards and keeping just the fields a model may use."""
from collections.abc import Mapping
from dataclasses import dataclass

from archetype_classifier.data_loading.dataset import CardCount, DeckContents
from archetype_classifier.data_loading.slices import DeckSet, SnapshotDeck


@dataclass(frozen=True)
class PredictDeck:
    """The only thing a model predicts on. It has no label, by design."""
    deck_id: int
    source: str
    maindeck: tuple[CardCount, ...]
    sideboard: tuple[CardCount, ...]

@dataclass(frozen=True)
class LabelledDeck:
    deck: PredictDeck
    label_id: int  # The label the deck is scored against.
    group_key: str  # The maindeck hash: identical maindecks are one piece of evidence.

def build_labelled_decks(deck_set: DeckSet, contents: Mapping[int, DeckContents]) -> list[LabelledDeck]:
    return [LabelledDeck(predict_deck(d, contents[d.deck_id]), d.label_id, d.maindeck_hash) for d in deck_set.decks.values()]  # type: ignore[arg-type]

def build_predict_decks(deck_set: DeckSet, contents: Mapping[int, DeckContents]) -> list[PredictDeck]:
    return [predict_deck(d, contents[d.deck_id]) for d in deck_set.decks.values()]

def predict_deck(deck: SnapshotDeck, contents: DeckContents) -> PredictDeck:
    return PredictDeck(deck.deck_id, deck.source, contents.maindeck, contents.sideboard)
