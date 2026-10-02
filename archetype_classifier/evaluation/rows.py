"""The rows of the results table: named, versioned groups of scored decks. Scores are never stored; they're recomputed from a run's guesses (decision F)."""
from collections.abc import Callable
from dataclasses import dataclass

from archetype_classifier.data_loading.labels import LabelStatus
from archetype_classifier.data_loading.slices import DeckSet, SnapshotDeck
from archetype_classifier.data_loading.splits import Split, SplitScheme

ROWS_VERSION = 1  # Bump on any change to which rows exist or which decks they hold.

@dataclass(frozen=True)
class Row:
    name: str
    splits: frozenset[Split]
    deck_ids: frozenset[int]

def build_rows(scored: DeckSet, training: DeckSet, scheme: SplitScheme) -> list[Row]:
    """The rows for the splits that were scored. Rows hold VERIFIED decks only."""
    training_maindecks = {d.maindeck_hash for d in training.decks.values()}
    rows: list[Row] = []
    for split, prefix in ((Split.HELD_OUT, 'held-out'), (Split.VALIDATION, 'validation')):
        if split not in scored.splits:
            continue
        decks = [d for d in scored.decks.values() if d.split == split and d.label_status == LabelStatus.VERIFIED]
        def row(name: str, keep: Callable[[SnapshotDeck], bool], split: Split = split, decks: list[SnapshotDeck] = decks) -> None:
            rows.append(Row(name, frozenset({split}), frozenset(d.deck_id for d in decks if keep(d))))
        if split == Split.HELD_OUT:
            row('held-out, no unseen cards', lambda d: d.unseen_maindeck_copies == 0)
            row('held-out, unseen cards', lambda d: d.unseen_maindeck_copies > 0)
        else:
            row(prefix, lambda d: True)
            row(f'{prefix}, new maindeck', lambda d: d.maindeck_hash not in training_maindecks)
            row(f'{prefix}, repeated maindeck', lambda d: d.maindeck_hash in training_maindecks)
    return rows
