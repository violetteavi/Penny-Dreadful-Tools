"""Deck diffs (#62; 20261024_Deck_Diffs_Architecture.pdf): a deck D against a training row T, whose label is the target archetype.

A diff goes copy by copy: a card at 4 copies in T and 2 in D keeps 2 and removes 2.

An axis runs from a contrast's centroid to the archetype's: u, the unit direction from mu_B to mu_A, with the gap |mu_A - mu_B| and each card's
alignment with u (signatures.build_push uses the same arithmetic).
"""
from dataclasses import dataclass

import numpy as np

from archetype_classifier.data_loading.dataset import CardCount
from archetype_classifier.geometry.space import DeckSpace


@dataclass(frozen=True)
class DeckDiff:
    kept: tuple[CardCount, ...]  # Copies in both, in name order.
    removed: tuple[CardCount, ...]  # T's copies that D lacks.
    added: tuple[CardCount, ...]  # D's copies that T lacks.

@dataclass(frozen=True)
class Axis:
    direction: np.ndarray  # u, unit length, in the space.
    gap: float  # |mu_A - mu_B|.
    alignment: np.ndarray  # Each card's alignment with u, in the space's card order.


def build_deck_diff(target: tuple[CardCount, ...], deck: tuple[CardCount, ...]) -> DeckDiff:
    before = {line.card: line.n for line in target}
    after = {line.card: line.n for line in deck}
    cards = sorted(before.keys() | after.keys())

    def lines(count: dict[str, int]) -> tuple[CardCount, ...]:
        return tuple(CardCount(card, count[card]) for card in cards if count.get(card, 0) > 0)
    return DeckDiff(lines({c: min(before.get(c, 0), after.get(c, 0)) for c in cards}), lines({c: before.get(c, 0) - after.get(c, 0) for c in cards}),
                    lines({c: after.get(c, 0) - before.get(c, 0) for c in cards}))


def build_axis(space: DeckSpace, archetype_shares: np.ndarray, contrast_shares: np.ndarray) -> Axis | None:
    """The axis in the space, with each card's alignment e_c . u (alpha); None when the two centroids coincide."""
    difference = space.vector(archetype_shares - contrast_shares)
    gap = float(np.linalg.norm(difference))
    if gap == 0:
        return None
    direction = difference / gap
    return Axis(direction, gap, space.alignment(direction))
