import hashlib
from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from archetype_classifier.data_loading.labels import LabelChange, LabelFacts, LabelStatus, label_facts
from archetype_classifier.data_loading.splits import Split, SplitScheme, assign_split


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
    reviewed: bool

@dataclass(frozen=True)
class DeckCardRow:
    deck_id: int
    card: str
    n: int
    sideboard: bool

@dataclass(frozen=True)
class DeckFacts:
    """One deck as the snapshot freezes it: facts only, before any split scheme decides how it's used."""
    deck_id: int
    season_id: int
    source: str
    reviewed: bool
    maindeck_hash: str | None  # Equal for decks with identical maindecks, whatever their sideboards; None with no maindeck cards.
    maindeck_cards: int
    labels: LabelFacts
    site_archetype_id: int | None  # The deck's label on the site when the snapshot was taken.

@dataclass(frozen=True)
class ArchetypeSnapshot:
    id: int
    name: str
    parent_id: int | None
    depth: int  # 0 for a top-level archetype.

@dataclass(frozen=True)
class Snapshot:
    decks: dict[int, DeckFacts]
    archetypes: dict[int, ArchetypeSnapshot]

def snapshot_decks(decks: Sequence[DeckRow], label_history: Iterable[LabelChange], deck_cards: Iterable[DeckCardRow], archetypes: Sequence[ArchetypeRow]) -> Snapshot:
    """Freeze every deck's facts, whatever its source, label or cards. Which decks are used is a split scheme's decision."""
    history_by_deck: dict[int, list[LabelChange]] = defaultdict(list)
    for change in label_history:
        history_by_deck[change.deck_id].append(change)
    maindeck_sums: dict[int, int] = defaultdict(int)
    maindeck_cards: dict[int, int] = defaultdict(int)
    for c in deck_cards:
        if not c.sideboard:
            maindeck_sums[c.deck_id] += line_digest(c)
            maindeck_cards[c.deck_id] += c.n
    snapshots = {}
    for d in decks:
        maindeck_hash = f'{maindeck_sums[d.id] % HASH_MODULUS:040x}' if maindeck_cards[d.id] else None
        snapshots[d.id] = DeckFacts(d.id, d.season_id, d.source, d.reviewed, maindeck_hash, maindeck_cards[d.id], label_facts(history_by_deck[d.id]), d.archetype_id)
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
        # Transitional, until split_decks assigns label statuses: keep the old behaviour.
        decision = assign_split(deck_id=d.deck_id, season_id=d.season_id, maindeck_hash=d.maindeck_hash, maindeck_cards=60, status=LabelStatus.VERIFIED, scheme=scheme)
        if decision.split != Split.EXCLUDED:
            splits[d.deck_id] = decision.split
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
