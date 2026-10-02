"""The rows of the results table: named, versioned groups of scored decks. Scores are never stored; they're recomputed from a run's guesses (decision F)."""
import logging
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from archetype_classifier.data_loading.labels import LabelStatus
from archetype_classifier.data_loading.slices import DeckSet, SnapshotDeck
from archetype_classifier.data_loading.splits import Split, SplitScheme
from archetype_classifier.evaluation import store
from archetype_classifier.evaluation.metrics import ArchetypeTree, ScoredDeck, Scores, score
from shared.database import Database

logger = logging.getLogger(__name__)

ROWS_VERSION = 1  # Bump on any change to which rows exist or which decks they hold.
PREFIXES = {Split.TRAIN: 'train', Split.HELD_OUT: 'held-out', Split.VALIDATION: 'validation', Split.TEST: 'test'}
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
    for split in (Split.TRAIN, Split.HELD_OUT, Split.VALIDATION, Split.TEST):
        if split not in scored.splits:
            continue
        decks = [d for d in scored.decks.values() if d.split == split]
        verified = [d for d in decks if d.label_status == LabelStatus.VERIFIED]
        for name, keep in split_rows(split, repeated, scheme):
            rows.append(Row(name, frozenset({split}), frozenset(d.deck_id for d in verified if keep(d))))
        allowed = scheme.train_statuses if split == Split.TRAIN else scheme.eval_statuses
        if LabelStatus.UNVERIFIED in allowed:
            rows.append(Row(f'{PREFIXES[split]}, unverified labels', frozenset({split}), frozenset(d.deck_id for d in decks if d.label_status == LabelStatus.UNVERIFIED)))
    for empty in (r for r in rows if not r.deck_ids):
        logger.info("Row '%s' has no decks, so it's left out", empty.name)  # The metrics module can't score an empty set.
    return [r for r in rows if r.deck_ids]

def split_rows(split: Split, repeated: Keep, scheme: SplitScheme) -> list[tuple[str, Keep]]:
    """Each row a split's scored decks fall into, as its name and which of the split's decks it keeps."""
    if split == Split.TRAIN:
        return [('train, in-sample', lambda d: True)]  # How well the model fits the decks it learned from; not a generalisation score.
    if split == Split.HELD_OUT:
        unseen: list[tuple[str, Keep]] = [('held-out, no unseen cards', lambda d: d.unseen_maindeck_copies == 0), ('held-out, unseen cards', lambda d: d.unseen_maindeck_copies > 0)]
        # Without twins, held-out decks never repeat a training maindeck, so maindeck rows would say nothing.
        return [*unseen, *maindeck_rows('held-out', repeated)] if scheme.allow_held_out_twins else unseen
    if split == Split.VALIDATION:
        return [('validation', lambda d: True), *maindeck_rows('validation', repeated)]
    bands: list[tuple[str, Keep]] = [(f'test, {label} unseen copies', in_band(low, high)) for label, low, high in UNSEEN_BANDS]
    return [('test, overall', lambda d: True), *bands, *maindeck_rows('test', repeated)]

def maindeck_rows(prefix: str, repeated: Keep) -> list[tuple[str, Keep]]:
    return [(f'{prefix}, new maindeck', lambda d: not repeated(d)), (f'{prefix}, repeated maindeck', repeated)]

def in_band(low: int, high: int | None) -> Keep:
    return lambda d: d.unseen_maindeck_copies >= low and (high is None or d.unseen_maindeck_copies <= high)

@dataclass(frozen=True)
class RowScores:
    scores: Scores
    trained_on: bool  # The model trained on this row's split, so its scores measure fit, not generalisation.
    tuned_on: bool  # The model tuned on this row's split, so its scores are optimistic.
    skipped: int  # Decks in the row with no stored guess.

def score_rows(edb: Database, run_id: int, tree: ArchetypeTree, scored: DeckSet, rows: Sequence[Row], training_splits: frozenset[Split],
               validation_splits: frozenset[Split], min_decks: int, include_test: bool = False) -> dict[str, RowScores]:
    """Score each row from a run's stored guesses. Flags are derived per deck, through its split, from the model's training and validation splits."""
    test_rows = [r.name for r in rows if Split.TEST in r.splits]
    if test_rows and not include_test:
        raise ValueError(f'Rows {test_rows} hold TEST decks, which are looked at rarely: pass include_test=True to score them')
    guesses = store.load_guesses(edb, run_id)
    results = {}
    for row in rows:
        missing = sorted(i for i in row.deck_ids if i not in guesses)
        if missing:
            logger.warning("Row '%s': skipped %d deck%s with no stored guess: %s", row.name, len(missing), '' if len(missing) == 1 else 's', missing)
        decks = [ScoredDeck(i, scored.decks[i].label_id, guesses[i].guess_id, scored.decks[i].maindeck_hash)  # type: ignore[arg-type]  # Scored decks always have a label and a maindeck.
                 for i in sorted(row.deck_ids) if i in guesses]
        if not decks:
            logger.warning("Row '%s' has no decks with a stored guess, so it's left out", row.name)
            continue
        results[row.name] = RowScores(score(tree, decks, min_decks), bool(row.splits & training_splits), bool(row.splits & validation_splits), len(missing))
    if test_rows:
        store.log_test_look(edb, run_id, test_rows)  # Every look at test results is recorded, at the moment scores are computed.
    return results
