"""The rows of the results table: named, versioned groups of scored decks. Scores are never stored; they're recomputed from a run's guesses (decision F)."""
from collections.abc import Callable
from dataclasses import dataclass

from archetype_classifier.data_loading.labels import LabelStatus
from archetype_classifier.data_loading.slices import DeckSet, SnapshotDeck
from archetype_classifier.data_loading.splits import Split, SplitScheme

ROWS_VERSION = 1  # Bump on any change to which rows exist or which decks they hold.
UNSEEN_BANDS = [('0', 0, 0), ('1–4', 1, 4), ('5–12', 5, 12), ('13+', 13, None)]  # Unseen maindeck copies: label, lowest, highest.

type Keep = Callable[[SnapshotDeck], bool]

@dataclass(frozen=True)
class Row:
    name: str
    splits: frozenset[Split]
    deck_ids: frozenset[int]

def build_rows(scored: DeckSet, training: DeckSet, scheme: SplitScheme) -> list[Row]:
    """The rows for the splits that were scored. Every row but the unverified one holds VERIFIED decks only."""
    training_maindecks = {d.maindeck_hash for d in training.decks.values()}
    def repeated(d: SnapshotDeck) -> bool:
        return d.maindeck_hash in training_maindecks
    rows = []
    for split in (Split.HELD_OUT, Split.VALIDATION, Split.TEST):
        if split not in scored.splits:
            continue
        verified = [d for d in scored.decks.values() if d.split == split and d.label_status == LabelStatus.VERIFIED]
        for name, keep in split_rows(split, repeated):
            rows.append(Row(name, frozenset({split}), frozenset(d.deck_id for d in verified if keep(d))))
    return rows

def split_rows(split: Split, repeated: Keep) -> list[tuple[str, Keep]]:
    """Each row a split's scored decks fall into, as its name and which of the split's decks it keeps."""
    if split == Split.HELD_OUT:
        return [('held-out, no unseen cards', lambda d: d.unseen_maindeck_copies == 0), ('held-out, unseen cards', lambda d: d.unseen_maindeck_copies > 0)]
    if split == Split.VALIDATION:
        return [('validation', lambda d: True), *maindeck_rows('validation', repeated)]
    bands: list[tuple[str, Keep]] = [(f'test, {label} unseen copies', in_band(low, high)) for label, low, high in UNSEEN_BANDS]
    return [('test, overall', lambda d: True), *bands, *maindeck_rows('test', repeated)]

def maindeck_rows(prefix: str, repeated: Keep) -> list[tuple[str, Keep]]:
    return [(f'{prefix}, new maindeck', lambda d: not repeated(d)), (f'{prefix}, repeated maindeck', repeated)]

def in_band(low: int, high: int | None) -> Keep:
    return lambda d: d.unseen_maindeck_copies >= low and (high is None or d.unseen_maindeck_copies <= high)
