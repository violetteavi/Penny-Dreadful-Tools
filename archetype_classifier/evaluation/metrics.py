"""Scores archetype guesses against the archetype tree with hierarchical precision, recall and F (ADR 0001)."""
from collections.abc import Mapping
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

    def lineage(self, archetype_id: int) -> frozenset[int]:
        """The archetype and its ancestors, not counting the root."""
        ids = set()
        current: int | None = archetype_id
        while current is not None:
            ids.add(current)
            current = self.archetypes[current].parent_id
        return frozenset(ids)

@dataclass(frozen=True)
class DeckScore:
    hp: float
    hr: float
    hf: float
    exact: bool

def score_deck(tree: ArchetypeTree, label_id: int, guess_id: int) -> DeckScore:
    label, guess = tree.lineage(label_id), tree.lineage(guess_id)
    shared = len(label & guess)
    hp, hr = shared / len(guess), shared / len(label)
    return DeckScore(hp, hr, f_measure(hp, hr), guess_id == label_id)

def f_measure(hp: float, hr: float) -> float:
    return 0.0 if hp + hr == 0 else 2 * hp * hr / (hp + hr)
