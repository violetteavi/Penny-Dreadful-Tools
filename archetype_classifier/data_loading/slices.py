"""Picking decks by split. The scheme has already put every deck in exactly one split, so this only selects."""
import hashlib
from collections.abc import Iterable
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
    deck_ids_hash: str  # A fingerprint of the deck ids, whatever their order; recorded on a model for its training and validation decks.

def build_deck_set(snapshot: Snapshot, splits: frozenset[Split], include_test: bool = False) -> DeckSet:
    """Exactly the decks in the requested splits. Excluded decks can't be picked, and test decks need include_test."""
    if Split.EXCLUDED in splits:
        raise ValueError('EXCLUDED decks are neither trained on nor scored, so they never form a deck set')
    if Split.TEST in splits and not include_test:
        raise ValueError('TEST decks are looked at rarely: pass include_test=True to pick them')
    decks = {i: d for i, d in snapshot.decks.items() if d.split in splits}
    return DeckSet(decks, splits, deck_ids_hash(decks))

def deck_ids_hash(deck_ids: Iterable[int]) -> str:
    return hashlib.sha1(','.join(str(i) for i in sorted(deck_ids)).encode()).hexdigest()
