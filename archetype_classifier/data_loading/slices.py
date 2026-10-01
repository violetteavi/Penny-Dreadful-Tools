"""Picking decks by split. The scheme has already put every deck in exactly one split, so this only selects."""
from dataclasses import dataclass

from archetype_classifier.data_loading.dataset import ArchetypeSnapshot
from archetype_classifier.data_loading.labels import LabelFacts, LabelStatus
from archetype_classifier.data_loading.splits import ExclusionReason, Split, SplitScheme


@dataclass(frozen=True)
class SnapshotDeck:
    """One deck as an experiment sees it: its frozen facts, and how its snapshot's scheme uses it."""
    deck_id: int
    season_id: int
    source: str
    maindeck_hash: str | None
    reviewed: bool
    split: Split
    exclusion_reason: ExclusionReason | None
    label_status: LabelStatus
    label_id: int | None  # The label the deck is scored against.
    unseen_maindeck_copies: int  # Against training maindecks only.
    labels: LabelFacts
    site_archetype_id: int | None

@dataclass(frozen=True)
class Snapshot:
    """Every deck in a snapshot under one split scheme, loaded once."""
    decks: dict[int, SnapshotDeck]
    archetypes: dict[int, ArchetypeSnapshot]
    scheme: SplitScheme

@dataclass(frozen=True)
class DeckSet:
    decks: dict[int, SnapshotDeck]
    splits: frozenset[Split]

def build_deck_set(snapshot: Snapshot, splits: frozenset[Split]) -> DeckSet:
    """Exactly the decks in the requested splits."""
    return DeckSet({i: d for i, d in snapshot.decks.items() if d.split in splits}, splits)
