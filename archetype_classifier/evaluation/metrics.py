"""Scores archetype guesses against the archetype tree with hierarchical precision, recall and F (ADR 0001)."""
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from statistics import fmean

from archetype_classifier.data_loading.dataset import ArchetypeSnapshot


@dataclass(frozen=True)
class ScoredDeck:
    deck_id: int
    label_id: int
    guess_id: int | None  # None is no guess, scored as a guess of the root.
    group_key: str  # The maindeck hash: decks sharing it are resampled together.

class ArchetypeTree:
    def __init__(self, archetypes: Mapping[int, ArchetypeSnapshot]) -> None:
        self.archetypes = archetypes

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
class DepthSummary:
    counts: Counter[int]  # Decks by depth difference.

    @property
    def mean(self) -> float | None:
        total = self.counts.total()
        return sum(k * n for k, n in self.counts.items()) / total if total else None

@dataclass(frozen=True)
class Scores:
    micro: Hierarchical
    macro: Hierarchical  # The mean over labelled archetypes with at least min_decks decks, of each value that is defined.
    min_decks: int
    macro_archetypes: int  # Labelled archetypes with at least min_decks decks.
    labelled_archetypes: int
    coverage: float  # The share of decks with a guess.
    exact_match_rate: float  # One minus this is the share of guesses a reviewer would change.
    on_path_depths: DepthSummary  # Below 0 are parent fallbacks, above 0 too-specific guesses.
    off_path_depths: DepthSummary

def score(tree: ArchetypeTree, decks: Sequence[ScoredDeck], min_decks: int) -> Scores:
    overlaps = [(d, overlap(tree, d.label_id, d.guess_id)) for d in decks]
    by_label: dict[int, list[Overlap]] = defaultdict(list)
    for d, o in overlaps:
        by_label[d.label_id].append(o)
    qualifying = [sum_overlaps(os).hierarchical() for os in by_label.values() if len(os) >= min_decks]
    macro = Hierarchical(fmean(h.hp for h in qualifying if h.hp is not None), fmean(h.hr for h in qualifying), fmean(h.hf for h in qualifying))
    coverage = sum(d.guess_id is not None for d in decks) / len(decks)
    exact_match_rate = sum(d.guess_id == d.label_id for d in decks) / len(decks)
    deck_scores = [score_deck(tree, d.label_id, d.guess_id) for d in decks]
    on_path = DepthSummary(Counter(s.depth_difference for s in deck_scores if s.on_path))
    off_path = DepthSummary(Counter(s.depth_difference for s in deck_scores if not s.on_path))
    return Scores(sum_overlaps(o for _, o in overlaps).hierarchical(), macro, min_decks, len(qualifying), len(by_label), coverage, exact_match_rate, on_path, off_path)

def sum_overlaps(overlaps: Iterable[Overlap]) -> Overlap:
    return sum(overlaps, Overlap(0, 0, 0))

def overlap(tree: ArchetypeTree, label_id: int, guess_id: int | None) -> Overlap:
    label, guess = tree.lineage(label_id), tree.lineage(guess_id)
    return Overlap(len(label & guess), len(guess), len(label))

def f_measure(hp: float | None, hr: float) -> float:
    return 0.0 if hp is None or hp + hr == 0 else 2 * hp * hr / (hp + hr)
