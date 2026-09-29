import hashlib
from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from archetype_classifier.data_loading.labels import HUMAN_PROVENANCES, LabelChange, Provenance, label_source
from archetype_classifier.data_loading.splits import Split, SplitScheme, assign_split

INCLUDED_SOURCES = frozenset({'League', 'Gatherling'})
EXCLUDED_ARCHETYPES = frozenset({'Unclassified', 'Commander'})  # Placeholders, not strategies.

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
    archetype_id: int | None

@dataclass(frozen=True)
class DeckCardRow:
    deck_id: int
    card: str
    n: int
    sideboard: bool

@dataclass(frozen=True)
class DeckSnapshot:
    deck_id: int
    season_id: int
    archetype_id: int  # The deck's label when the snapshot was taken.
    provenance: Provenance
    guess_archetype_id: int | None
    ground_truth: bool
    maindeck_hash: str  # Equal for decks with identical maindecks, whatever their sideboards.

@dataclass(frozen=True)
class ArchetypeSnapshot:
    id: int
    name: str
    parent_id: int | None
    depth: int  # 0 for a top-level archetype.

@dataclass(frozen=True)
class Snapshot:
    decks: dict[int, DeckSnapshot]
    archetypes: dict[int, ArchetypeSnapshot]

def snapshot_decks(decks: Sequence[DeckRow], label_history: Iterable[LabelChange], deck_cards: Iterable[DeckCardRow], archetypes: Sequence[ArchetypeRow]) -> Snapshot:
    """Freeze each deck's label and where it came from."""
    history_by_deck: dict[int, list[LabelChange]] = defaultdict(list)
    for change in label_history:
        history_by_deck[change.deck_id].append(change)
    decks_with_cards: set[int] = set()
    maindeck_sums: dict[int, int] = defaultdict(int)
    for c in deck_cards:
        decks_with_cards.add(c.deck_id)
        if not c.sideboard:
            maindeck_sums[c.deck_id] += line_digest(c)
    excluded_ids = {a.id for a in archetypes if a.name in EXCLUDED_ARCHETYPES}
    snapshots = {}
    for d in decks:
        if d.archetype_id is None or d.archetype_id in excluded_ids or d.source not in INCLUDED_SOURCES or d.id not in decks_with_cards:
            continue
        source = label_source(history_by_deck[d.id])
        ground_truth = source.provenance in HUMAN_PROVENANCES and source.latest_archetype_id == d.archetype_id
        maindeck_hash = f'{maindeck_sums[d.id] % HASH_MODULUS:040x}'
        snapshots[d.id] = DeckSnapshot(d.id, d.season_id, d.archetype_id, source.provenance, source.guess_archetype_id, ground_truth, maindeck_hash)
    return Snapshot(snapshots, freeze_archetypes(archetypes))

@dataclass(frozen=True)
class DeckSplit:
    deck_id: int
    split: Split
    unseen_maindeck_copies: int  # Maindeck copies of cards that appear in no training maindeck.

def split_decks(snapshot: Snapshot, deck_cards: Iterable[DeckCardRow], scheme: SplitScheme) -> dict[int, DeckSplit]:
    """Apply a split scheme to a snapshot. Decks whose season is outside the scheme are left out."""
    splits = {}
    for d in snapshot.decks.values():
        split = assign_split(d.season_id, d.maindeck_hash, scheme)
        if split is not None:
            splits[d.deck_id] = split
    seen_cards: set[str] = set()
    other_maindecks: dict[int, list[DeckCardRow]] = defaultdict(list)
    for c in deck_cards:
        split = splits.get(c.deck_id)
        if split is None or c.sideboard:
            continue
        if split == Split.TRAIN:
            seen_cards.add(c.card)
        else:
            other_maindecks[c.deck_id].append(c)
    return {deck_id: DeckSplit(deck_id, split, sum(c.n for c in other_maindecks[deck_id] if c.card not in seen_cards)) for deck_id, split in splits.items()}

HASH_MODULUS = 2 ** 160

def line_digest(c: DeckCardRow) -> int:
    """One maindeck line's contribution to its deck's hash. Summing these makes the hash independent of card order."""
    return int.from_bytes(hashlib.sha1(f'{c.n} {c.card}'.encode()).digest(), 'big')

def freeze_archetypes(archetypes: Sequence[ArchetypeRow]) -> dict[int, ArchetypeSnapshot]:
    parents = {a.id: a.parent_id for a in archetypes}
    def depth(archetype_id: int) -> int:
        parent_id = parents[archetype_id]
        return 0 if parent_id is None else depth(parent_id) + 1
    return {a.id: ArchetypeSnapshot(a.id, a.name, a.parent_id, depth(a.id)) for a in archetypes}
