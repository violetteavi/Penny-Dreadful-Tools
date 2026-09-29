from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from archetype_classifier.data_loading.labels import HUMAN_PROVENANCES, LabelChange, label_source


@dataclass(frozen=True)
class ArchetypeRow:
    id: int
    name: str
    parent_id: int | None

@dataclass(frozen=True)
class DeckRow:
    id: int
    season_id: int
    source: str
    archetype_id: int

@dataclass(frozen=True)
class DeckCardRow:
    deck_id: int
    card: str
    n: int
    sideboard: bool

@dataclass(frozen=True)
class DeckSnapshot:
    deck_id: int
    guess_archetype_id: int | None
    ground_truth: bool

@dataclass(frozen=True)
class Snapshot:
    decks: dict[int, DeckSnapshot]

def snapshot_decks(decks: Sequence[DeckRow], label_history: Iterable[LabelChange], deck_cards: Iterable[DeckCardRow], archetypes: Sequence[ArchetypeRow]) -> Snapshot:
    """Freeze each deck's label and where it came from."""
    history_by_deck: dict[int, list[LabelChange]] = defaultdict(list)
    for change in label_history:
        history_by_deck[change.deck_id].append(change)
    snapshots = {}
    for d in decks:
        source = label_source(history_by_deck[d.id])
        snapshots[d.id] = DeckSnapshot(d.id, source.guess_archetype_id, ground_truth=source.provenance in HUMAN_PROVENANCES)
    return Snapshot(snapshots)
