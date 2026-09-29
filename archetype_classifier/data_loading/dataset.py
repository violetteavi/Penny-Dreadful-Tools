import hashlib
from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from archetype_classifier.data_loading.labels import HUMAN_PROVENANCES, LabelChange, Provenance, label_source

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
class Snapshot:
    decks: dict[int, DeckSnapshot]

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
    return Snapshot(snapshots)

HASH_MODULUS = 2 ** 160

def line_digest(c: DeckCardRow) -> int:
    """One maindeck line's contribution to its deck's hash. Summing these makes the hash independent of card order."""
    return int.from_bytes(hashlib.sha1(f'{c.n} {c.card}'.encode()).digest(), 'big')
