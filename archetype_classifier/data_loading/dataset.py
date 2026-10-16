import hashlib
import logging
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

from archetype_classifier.data_loading.labels import DeckLabel, LabelChange, LabelFacts, LabelStatus, decided_after, label_at, label_facts, label_status
from archetype_classifier.data_loading.splits import ExclusionReason, Split, SplitDecision, SplitScheme, assign_split, deck_role, group_key

logger = logging.getLogger(__name__)


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
class CardCount:
    card: str
    n: int

@dataclass(frozen=True)
class DeckContents:
    """A deck's cards, read live from the site database: past decks never change, so they're never copied."""
    maindeck: tuple[CardCount, ...]
    sideboard: tuple[CardCount, ...]

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
class SnapshotFacts:
    decks: dict[int, DeckFacts]
    archetypes: dict[int, ArchetypeSnapshot]

def snapshot_decks(decks: Sequence[DeckRow], label_history: Iterable[LabelChange], deck_cards: Iterable[DeckCardRow], archetypes: Sequence[ArchetypeRow]) -> SnapshotFacts:
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
    return SnapshotFacts(snapshots, freeze_archetypes(archetypes))

@dataclass(frozen=True)
class DeckSplit:
    """How one deck is used under a split scheme."""
    deck_id: int
    split: Split
    reason: ExclusionReason | None  # Why the deck is excluded; None for every other split.
    label_status: LabelStatus
    label_id: int | None  # The label the deck is scored against.
    unseen_maindeck_copies: int  # Maindeck copies of cards that appear in no training maindeck.

@dataclass(frozen=True)
class TwinOverlap:
    """A maindeck that is both trained on and held out, which the default scheme should never produce."""
    maindeck_hash: str
    train_deck_ids: frozenset[int]
    held_out_deck_ids: frozenset[int]

@dataclass(frozen=True)
class SplitReport:
    by_split: Counter[Split]
    by_reason: Counter[ExclusionReason]
    twin_overlaps: list[TwinOverlap]
    cutoff_labels: Counter[str]  # TRAIN-role decks decided after the label cutoff: 'same label', 'different label', 'no label' or 'out of scope'.

@dataclass(frozen=True)
class Splits:
    decks: dict[int, DeckSplit]
    report: SplitReport

def split_decks(snapshot: SnapshotFacts, deck_cards: Iterable[DeckCardRow], scheme: SplitScheme, history: Mapping[int, Sequence[LabelChange]] | None = None) -> Splits:
    """Put every deck in exactly one split. Unseen cards are counted against training maindecks only, so excluded decks change nothing.

    Under a label cutoff, a TRAIN-role deck with a label decision after it takes its label from its history as it stood then; every other deck keeps
    the label rule's label. The history is needed only then."""
    if scheme.label_cutoff is not None and history is None:
        raise ValueError(f"Scheme '{scheme.name}' has a label cutoff, so splitting needs the snapshot's label history")
    cutoff = datetime.fromtimestamp(scheme.label_cutoff, UTC) if scheme.label_cutoff is not None else None
    names = {a.id: a.name for a in snapshot.archetypes.values()}
    labels: dict[int, DeckLabel] = {}
    decisions: dict[int, SplitDecision] = {}
    cutoff_labels: Counter[str] = Counter()
    for d in snapshot.decks.values():
        deck_history = history.get(d.deck_id, ()) if history is not None else ()
        if cutoff is not None and d.maindeck_hash is not None and deck_role(d.season_id, group_key(d.deck_id, d.maindeck_hash, scheme), scheme) == Split.TRAIN and decided_after(deck_history, cutoff):
            labels[d.deck_id] = label_at(deck_history, cutoff, d.source, names, scheme.scope_rule)
            cutoff_labels[cutoff_kind(labels[d.deck_id], d.site_archetype_id)] += 1
        else:
            archetype = snapshot.archetypes.get(d.site_archetype_id) if d.site_archetype_id is not None else None
            labels[d.deck_id] = label_status(d.labels, d.site_archetype_id, archetype.name if archetype else None, d.source, scheme.scope_rule, scheme.label_rule)
        decisions[d.deck_id] = assign_split(deck_id=d.deck_id, season_id=d.season_id, maindeck_hash=d.maindeck_hash, maindeck_cards=d.maindeck_cards,
                                            status=labels[d.deck_id].status, scheme=scheme)
    seen_cards: set[str] = set()
    other_maindecks: dict[int, list[DeckCardRow]] = defaultdict(list)
    for c in deck_cards:
        if c.sideboard or c.deck_id not in decisions:
            continue
        if decisions[c.deck_id].split == Split.TRAIN:
            seen_cards.add(c.card)
        else:
            other_maindecks[c.deck_id].append(c)
    decks = {deck_id: DeckSplit(deck_id, decision.split, decision.reason, labels[deck_id].status, labels[deck_id].label_id,
                                sum(c.n for c in other_maindecks[deck_id] if c.card not in seen_cards))
             for deck_id, decision in decisions.items()}
    hashes = {d.deck_id: d.maindeck_hash for d in snapshot.decks.values() if d.maindeck_hash is not None}
    for kind, n in sorted(cutoff_labels.items()):
        logger.info('Label cutoff: %d training deck%s decided after it got %s', n, '' if n == 1 else 's', kind)
    report = SplitReport(Counter(s.split for s in decks.values()), Counter(s.reason for s in decks.values() if s.reason is not None), twin_overlaps(decks, hashes, scheme),
                         cutoff_labels)
    return Splits(decks, report)

def cutoff_kind(label: DeckLabel, site_archetype_id: int | None) -> str:
    """How a deck's label at the cutoff compares with its site label, for the split report."""
    if label.status == LabelStatus.OUT_OF_SCOPE:
        return 'out of scope'
    if label.status == LabelStatus.UNLABELLED:
        return 'no label'
    return 'same label' if label.label_id == site_archetype_id else 'different label'

def twin_overlaps(splits: Mapping[int, DeckSplit], maindeck_hashes: Mapping[int, str], scheme: SplitScheme) -> list[TwinOverlap]:
    """Maindecks in both TRAIN and HELD_OUT. Expected when twins are allowed; otherwise each is logged, and the split carries on."""
    if scheme.allow_held_out_twins:
        return []
    by_hash: dict[str, dict[Split, set[int]]] = defaultdict(lambda: defaultdict(set))
    for deck_id, s in splits.items():
        if s.split in (Split.TRAIN, Split.HELD_OUT) and deck_id in maindeck_hashes:
            by_hash[maindeck_hashes[deck_id]][s.split].add(deck_id)
    overlaps = [TwinOverlap(h, frozenset(groups[Split.TRAIN]), frozenset(groups[Split.HELD_OUT])) for h, groups in sorted(by_hash.items()) if groups[Split.TRAIN] and groups[Split.HELD_OUT]]
    for o in overlaps:
        logger.warning('Maindeck %s is in both TRAIN (decks %s) and HELD_OUT (decks %s)', o.maindeck_hash, sorted(o.train_deck_ids), sorted(o.held_out_deck_ids))
    return overlaps

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
