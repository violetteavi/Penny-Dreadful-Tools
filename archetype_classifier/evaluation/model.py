"""What a model sees. A deck set picks the decks; these functions only change their shape, attaching each deck's cards and keeping just the fields a model may use."""
import logging
from collections.abc import Mapping
from dataclasses import dataclass

from archetype_classifier.data_loading.dataset import CardCount, DeckContents
from archetype_classifier.data_loading.labels import LabelStatus
from archetype_classifier.data_loading.slices import DeckSet, SnapshotDeck

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PredictDeck:
    """The only thing a model predicts on. It has no label, by design."""
    deck_id: int
    source: str
    maindeck: tuple[CardCount, ...]
    sideboard: tuple[CardCount, ...]

@dataclass(frozen=True)
class TrainingDeck:
    deck: PredictDeck
    season_id: int
    archetype_id: int | None  # The site's current label, as the site's own guesser searches.
    reviewed: bool
    label_status: LabelStatus  # So a model trained on several statuses can tell them apart.

@dataclass(frozen=True)
class LabelledDeck:
    deck: PredictDeck
    label_id: int  # The label the deck is scored against.
    group_key: str  # The maindeck hash: identical maindecks are one piece of evidence.

def build_training_decks(deck_set: DeckSet, contents: Mapping[int, DeckContents]) -> list[TrainingDeck]:
    return [TrainingDeck(predict_deck(d, c), d.season_id, d.site_archetype_id, d.reviewed, d.label_status) for d, c in with_contents(deck_set, contents)]

def build_labelled_decks(deck_set: DeckSet, contents: Mapping[int, DeckContents]) -> list[LabelledDeck]:
    """Decks with the label each is scored against. A deck with no label, which only a training deck set can hold, is skipped with a warning."""
    labelled = []
    unlabelled = []
    for d, c in with_contents(deck_set, contents):
        if d.label_id is None or d.maindeck_hash is None:
            unlabelled.append(d.deck_id)
        else:
            labelled.append(LabelledDeck(predict_deck(d, c), d.label_id, d.maindeck_hash))
    if unlabelled:
        logger.warning('Skipped %d deck%s with no label: %s', len(unlabelled), plural(unlabelled), sorted(unlabelled))
    return labelled

def build_predict_decks(deck_set: DeckSet, contents: Mapping[int, DeckContents]) -> list[PredictDeck]:
    return [predict_deck(d, c) for d, c in with_contents(deck_set, contents)]

def with_contents(deck_set: DeckSet, contents: Mapping[int, DeckContents]) -> list[tuple[SnapshotDeck, DeckContents]]:
    """Each deck with its cards. A deck with none, for example one deleted from the site after the snapshot, is skipped with a warning."""
    missing = sorted(i for i in deck_set.decks if i not in contents)
    if missing:
        logger.warning('Skipped %d deck%s with no contents: %s', len(missing), plural(missing), missing)
    return [(d, contents[d.deck_id]) for d in deck_set.decks.values() if d.deck_id in contents]

def predict_deck(deck: SnapshotDeck, contents: DeckContents) -> PredictDeck:
    """Card lines sorted by name, so the same deck always gives the same input whatever order its rows were read in."""
    return PredictDeck(deck.deck_id, deck.source, sorted_lines(contents.maindeck), sorted_lines(contents.sideboard))

def sorted_lines(lines: tuple[CardCount, ...]) -> tuple[CardCount, ...]:
    return tuple(sorted(lines, key=lambda c: c.card))

def plural(items: list[int]) -> str:
    return '' if len(items) == 1 else 's'
