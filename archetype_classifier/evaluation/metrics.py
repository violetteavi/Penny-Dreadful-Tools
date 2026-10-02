"""Scores archetype guesses against the archetype tree with hierarchical precision, recall and F (ADR 0001)."""
import dataclasses
import logging
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from statistics import fmean

import numpy as np

from archetype_classifier.data_loading.dataset import ArchetypeSnapshot

logger = logging.getLogger(__name__)

METRICS_VERSION = 1  # Bump on any change to how a metric is computed; every report records it.
DEFAULT_SEED = 20260930
DEFAULT_RESAMPLES = 1000


@dataclass(frozen=True)
class ScoredDeck:
    deck_id: int
    label_id: int
    guess_id: int | None  # None is no guess, scored as a guess of the root.
    group_key: str  # The maindeck hash: decks sharing it are resampled together.

class ArchetypeTree:
    def __init__(self, archetypes: Mapping[int, ArchetypeSnapshot]) -> None:
        self.archetypes = archetypes

    def __contains__(self, archetype_id: int | None) -> bool:
        return archetype_id is None or archetype_id in self.archetypes

    def lineage(self, archetype_id: int | None) -> frozenset[int]:
        """The archetype and its ancestors, not counting the root. No guess (the root) has an empty lineage."""
        ids = set()
        current = archetype_id
        while current is not None:
            ids.add(current)
            current = self.archetypes[current].parent_id
        return frozenset(ids)

@dataclass(frozen=True)
class DeckScore:
    hp: float | None  # Undefined for no guess, which has no guessed archetypes to be right or wrong about.
    hr: float
    hf: float
    exact: bool
    depth_difference: int  # Guess depth minus label depth. Top-level archetypes have depth 0 and the root -1.
    on_path: bool  # The guess is the label, one of its ancestors (the root included) or one of its descendants.

@dataclass(frozen=True)
class Hierarchical:
    hp: float | None  # Undefined when nothing was guessed.
    hr: float
    hf: float

@dataclass(frozen=True)
class Overlap:
    """Archetype counts after expanding the guess and the label with their ancestors. Summing these over decks gives micro averages."""
    shared: int
    guessed: int
    labelled: int

    def __add__(self, other: 'Overlap') -> 'Overlap':
        return Overlap(self.shared + other.shared, self.guessed + other.guessed, self.labelled + other.labelled)

    def hierarchical(self) -> Hierarchical:
        hp, hr = (self.shared / self.guessed if self.guessed else None), self.shared / self.labelled
        return Hierarchical(hp, hr, f_measure(hp, hr))

def score_deck(tree: ArchetypeTree, label_id: int, guess_id: int | None) -> DeckScore:
    label, guess = tree.lineage(label_id), tree.lineage(guess_id)
    h = overlap(tree, label_id, guess_id).hierarchical()
    return DeckScore(h.hp, h.hr, h.hf, guess_id == label_id, len(guess) - len(label), guess <= label or label <= guess)

@dataclass(frozen=True)
class Interval:
    """The middle 95% of the bootstrap values."""
    low: float
    high: float

@dataclass(frozen=True)
class HierarchicalIntervals:
    hp: Interval
    hr: Interval
    hf: Interval

@dataclass(frozen=True)
class DepthSummary:
    counts: Counter[int]  # Decks by depth difference.

    @property
    def mean(self) -> float | None:
        total = self.counts.total()
        return sum(k * n for k, n in self.counts.items()) / total if total else None

@dataclass(frozen=True)
class Confusion:
    label_id: int
    guess_id: int | None
    decks: int
    on_path: bool

@dataclass(frozen=True)
class Scores:
    decks: int
    maindecks: int  # Distinct maindecks among the decks: the units the bootstrap resamples.
    micro: Hierarchical
    micro_intervals: HierarchicalIntervals
    seed: int
    resamples: int
    macro: Hierarchical | None  # The mean over labelled archetypes with at least min_decks decks, of each value that is defined. None when no archetype qualifies.
    min_decks: int
    macro_archetypes: int  # Labelled archetypes with at least min_decks decks.
    labelled_archetypes: int
    coverage: float  # The share of decks with a guess.
    exact_match_rate: float  # One minus this is the share of guesses a reviewer would change.
    on_path_depths: DepthSummary  # Below 0 are parent fallbacks, above 0 too-specific guesses.
    off_path_depths: DepthSummary
    confusions: list[Confusion]  # Every non-exact (label, guess) pair, most common first.
    skipped_decks: int  # Decks whose label or guess isn't in the tree. Nothing else counts them.
    missing_archetype_ids: frozenset[int]

def score(tree: ArchetypeTree, decks: Sequence[ScoredDeck], min_decks: int, seed: int = DEFAULT_SEED, resamples: int = DEFAULT_RESAMPLES) -> Scores:
    decks, skipped, missing = in_tree(tree, decks)
    if not decks:
        raise ValueError(f'No decks to score: {skipped} were given, and all were skipped')
    overlaps = [(d, overlap(tree, d.label_id, d.guess_id)) for d in decks]
    by_label: dict[int, list[Overlap]] = defaultdict(list)
    for d, o in overlaps:
        by_label[d.label_id].append(o)
    qualifying = [sum_overlaps(os).hierarchical() for os in by_label.values() if len(os) >= min_decks]
    macro = macro_average(qualifying)
    if macro is None:
        logger.warning('No labelled archetype has %d decks, so macro averages are undefined', min_decks)
    coverage = sum(d.guess_id is not None for d in decks) / len(decks)
    exact_match_rate = sum(d.guess_id == d.label_id for d in decks) / len(decks)
    deck_scores = [score_deck(tree, d.label_id, d.guess_id) for d in decks]
    on_path = DepthSummary(Counter(s.depth_difference for s in deck_scores if s.on_path))
    off_path = DepthSummary(Counter(s.depth_difference for s in deck_scores if not s.on_path))
    pairs = Counter((d.label_id, d.guess_id) for d in decks if d.guess_id != d.label_id)
    confusions = [Confusion(label_id, guess_id, n, score_deck(tree, label_id, guess_id).on_path) for (label_id, guess_id), n in pairs.most_common()]
    groups = maindeck_sums(decks, [o for _, o in overlaps])
    draws = bootstrap_sums(groups, seed, resamples)
    return Scores(len(decks), len(groups), sum_overlaps(o for _, o in overlaps).hierarchical(), micro_intervals(draws), seed, resamples, macro, min_decks, len(qualifying), len(by_label), coverage, exact_match_rate, on_path, off_path, confusions, skipped, missing)

SHARED, GUESSED, LABELLED, EXACT, DECKS = range(5)

def maindeck_sums(decks: Sequence[ScoredDeck], overlaps: Sequence[Overlap]) -> np.ndarray:
    """One row per maindeck, in order of first appearance: shared, guessed and labelled archetype counts, exact matches and decks, summed over its decks."""
    rows: dict[str, list[int]] = {}
    for d, o in zip(decks, overlaps, strict=True):
        row = rows.setdefault(d.group_key, [0] * 5)
        row[SHARED] += o.shared
        row[GUESSED] += o.guessed
        row[LABELLED] += o.labelled
        row[EXACT] += d.guess_id == d.label_id
        row[DECKS] += 1
    return np.array(list(rows.values()), dtype=float).reshape(-1, 5)

def bootstrap_sums(groups: np.ndarray, seed: int, resamples: int) -> np.ndarray:
    """One row per resample: the column sums over as many maindecks as there are, drawn with replacement."""
    rng = np.random.default_rng(seed)
    n = len(groups)
    return np.array([np.bincount(rng.integers(0, n, n), minlength=n) @ groups for _ in range(resamples)])

def rates(sums: np.ndarray) -> dict[str, np.ndarray]:
    """Micro hP, hR and hF and exact-match rate for each row of summed maindeck columns. hP is NaN when nothing was guessed."""
    with np.errstate(divide='ignore', invalid='ignore'):
        hp = sums[:, SHARED] / sums[:, GUESSED]
        hr = sums[:, SHARED] / sums[:, LABELLED]
        hf = np.where(hp + hr > 0, 2 * hp * hr / (hp + hr), 0.0)
    return {'hp': hp, 'hr': hr, 'hf': hf, 'exact_match_rate': sums[:, EXACT] / sums[:, DECKS]}

def micro_intervals(draws: np.ndarray) -> HierarchicalIntervals:
    r = rates(draws)
    return HierarchicalIntervals(interval(r['hp']), interval(r['hr']), interval(r['hf']))

def interval(values: np.ndarray) -> Interval:
    low, high = np.nanpercentile(values, [2.5, 97.5])
    return Interval(float(low), float(high))

def in_tree(tree: ArchetypeTree, decks: Sequence[ScoredDeck]) -> tuple[list[ScoredDeck], int, frozenset[int]]:
    """The decks whose label and guess are both in the tree, how many were skipped, and the missing archetype ids. Skipping is logged, not fatal."""
    kept = [d for d in decks if d.label_id in tree and d.guess_id in tree]
    missing = frozenset(a for d in decks for a in (d.label_id, d.guess_id) if a not in tree and a is not None)
    if missing:
        logger.warning('Skipped %d decks whose label or guess is not in the archetype tree; missing archetype ids: %s', len(decks) - len(kept), sorted(missing))
    return kept, len(decks) - len(kept), missing

def macro_average(per_archetype: Sequence[Hierarchical]) -> Hierarchical | None:
    if not per_archetype:
        return None
    hps = [h.hp for h in per_archetype if h.hp is not None]
    return Hierarchical(fmean(hps) if hps else None, fmean(h.hr for h in per_archetype), fmean(h.hf for h in per_archetype))

def sum_overlaps(overlaps: Iterable[Overlap]) -> Overlap:
    return sum(overlaps, Overlap(0, 0, 0))

def overlap(tree: ArchetypeTree, label_id: int, guess_id: int | None) -> Overlap:
    label, guess = tree.lineage(label_id), tree.lineage(guess_id)
    return Overlap(len(label & guess), len(guess), len(label))

def f_measure(hp: float | None, hr: float) -> float:
    return 0.0 if hp is None or hp + hr == 0 else 2 * hp * hr / (hp + hr)

@dataclass(frozen=True)
class Difference:
    """B minus A."""
    hp: float
    hr: float
    hf: float
    exact_match_rate: float

@dataclass(frozen=True)
class DifferenceIntervals:
    hp: Interval
    hr: Interval
    hf: Interval
    exact_match_rate: Interval

@dataclass(frozen=True)
class Comparison:
    difference: Difference
    intervals: DifferenceIntervals  # Each resample draws the same maindecks for both models.
    decks: int  # Decks both models were scored on.
    left_out: int  # Decks only one model was scored on: skipped for the other, or missing from its guesses.
    seed: int
    resamples: int

def compare(tree: ArchetypeTree, a: Sequence[ScoredDeck], b: Sequence[ScoredDeck], seed: int = DEFAULT_SEED, resamples: int = DEFAULT_RESAMPLES) -> Comparison:
    """Model B's micro scores minus model A's on the same decks, with paired bootstrap intervals."""
    a, _, _ = in_tree(tree, a)
    b_kept, _, _ = in_tree(tree, b)
    b_by_id = {d.deck_id: d for d in b_kept}
    shared_ids = b_by_id.keys() & {d.deck_id for d in a}
    left_out = len(a) + len(b_kept) - 2 * len(shared_ids)
    if left_out:
        logger.warning('Comparison: %d decks scored for only one model were left out', left_out)
    a = [d for d in a if d.deck_id in shared_ids]
    if not a:
        raise ValueError('No decks to compare: the two models have no scored decks in common')
    b_aligned = [dataclasses.replace(b_by_id[d.deck_id], group_key=d.group_key) for d in a]
    groups_a = maindeck_sums(a, [overlap(tree, d.label_id, d.guess_id) for d in a])
    groups_b = maindeck_sums(b_aligned, [overlap(tree, d.label_id, d.guess_id) for d in b_aligned])
    draws = bootstrap_sums(np.hstack([groups_a, groups_b]), seed, resamples)
    width = groups_a.shape[1]
    point_a, point_b = rates(groups_a.sum(axis=0, keepdims=True)), rates(groups_b.sum(axis=0, keepdims=True))
    draws_a, draws_b = rates(draws[:, :width]), rates(draws[:, width:])
    names = ('hp', 'hr', 'hf', 'exact_match_rate')
    difference = Difference(*(float(point_b[n][0] - point_a[n][0]) for n in names))
    intervals = DifferenceIntervals(*(interval(draws_b[n] - draws_a[n]) for n in names))
    return Comparison(difference, intervals, len(a), left_out, seed, resamples)
