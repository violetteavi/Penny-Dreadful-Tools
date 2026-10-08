"""What a model sees. A deck set picks the decks; these functions only change their shape, attaching each deck's cards and keeping just the fields a model may use."""
import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar, Protocol

from archetype_classifier.data_loading.dataset import CardCount, DeckContents
from archetype_classifier.data_loading.labels import LabelStatus
from archetype_classifier.data_loading.slices import DeckSet, SnapshotDeck
from archetype_classifier.evaluation.metrics import ArchetypeTree

logger = logging.getLogger(__name__)

type JSON = str | int | float | bool | None | list[JSON] | dict[str, JSON]


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

@dataclass(frozen=True)
class FitContext:
    """Fit-time extras, gathered so that adding one never changes fit's signature."""
    tree: ArchetypeTree
    legal_cards: Mapping[int, frozenset[str]]  # Season id -> the cards legal that season.
    seed: int
    embeddings_dir: Path | None = None  # Where a model finds its card embeddings; None is the standard embeddings/ folder. Not part of a model's identity.

@dataclass(frozen=True)
class Prediction:
    deck_id: int
    guess_id: int | None  # One guess per deck; None for no guess.
    evidence: dict[str, JSON]  # What the guess rests on, so a report can trace it.

class Model(Protocol):
    """Every model is fitted, predicts, and saves what fitting learned through this one contract.

    A model that tunes a threshold on its validation decks keeps the curve in its state under 'validation_curve': a list of
    [threshold, hP, hR, hF] points, with the chosen threshold under 'threshold'. Reports show it when it's there. This is a
    convention until a second tuned model shows what a shared validation step should look like (#33).
    """
    name: ClassVar[str]
    version: ClassVar[int]  # Bumped by hand when behaviour changes.
    params: dict[str, JSON]

    def fit(self, training: Sequence[TrainingDeck], validation: Sequence[LabelledDeck], context: FitContext) -> None: ...

    def predict(self, decks: Sequence[PredictDeck]) -> list[Prediction]: ...

    def state(self) -> dict[str, JSON]: ...

    @classmethod
    def from_state(cls, params: dict[str, JSON], state: dict[str, JSON], training: Sequence[TrainingDeck], context: FitContext) -> 'Model': ...

MODELS: dict[str, type[Model]] = {}

def register[M: Model](cls: type[M]) -> type[M]:
    """Make a model class findable by its name, which is all a stored model records about its class."""
    MODELS[cls.name] = cls
    return cls

def model_class(name: str) -> type[Model]:
    if name not in MODELS:
        raise KeyError(f'No model named {name!r}; registered models are {sorted(MODELS)}')
    return MODELS[name]

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
