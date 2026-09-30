"""Scores archetype guesses against the archetype tree with hierarchical precision, recall and F (ADR 0001)."""
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

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
class Scores:
    micro: Hierarchical

def score(tree: ArchetypeTree, decks: Sequence[ScoredDeck]) -> Scores:
    total = sum((overlap(tree, d.label_id, d.guess_id) for d in decks), Overlap(0, 0, 0))
    return Scores(total.hierarchical())

def overlap(tree: ArchetypeTree, label_id: int, guess_id: int | None) -> Overlap:
    label, guess = tree.lineage(label_id), tree.lineage(guess_id)
    return Overlap(len(label & guess), len(guess), len(label))

def f_measure(hp: float | None, hr: float) -> float:
    return 0.0 if hp is None or hp + hr == 0 else 2 * hp * hr / (hp + hr)
