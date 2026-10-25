"""Deck diffs (#62; 20261024_Deck_Diffs_Architecture.pdf): a deck D against a training row T, whose label is the target archetype.

A diff goes copy by copy: a card at 4 copies in T and 2 in D keeps 2 and removes 2.

An axis runs from a contrast's centroid to the archetype's: u, the unit direction from mu_B to mu_A, with the gap |mu_A - mu_B| and each card's
alignment with u (signatures.build_push uses the same arithmetic).

The shift is how far D moved along an axis: (v_D - v_T) . u = sum_c (l_c^D - l_c^T) x alignment_c, over the decks' scaled lines l. Positive means D
moved toward the archetype. It's exact and splits card by card; on the share axis (beta) it's the share shift.

The net shift is how much changed in any direction: |raw_D - raw_T| over the mean of the two decks' lengths, raw being a deck's vector before scaling
to unit length. Kept copies cancel in the difference, and the mean length makes it symmetric and comparable across spaces.
"""
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from scipy import stats

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

@dataclass(frozen=True)
class Shift:
    raw: float  # (v_D - v_T) . u.
    fraction: float  # raw / the gap.
    on_axis: float | None  # |raw| / how far D moved at all; None when it didn't.

@dataclass(frozen=True)
class CardContribution:
    card: str
    copies_target: int
    copies_deck: int
    contribution: float  # (l_c^D - l_c^T) x the card's alignment.

@dataclass(frozen=True)
class Contributions:
    cards: list[CardContribution]  # Every card whose copies changed, in name order.
    rescaling: float  # The kept cards, whose copies didn't change: their lines still move when the deck's length does.

@dataclass(frozen=True)
class Agreement:
    pairs: int  # Pairs with both shifts.
    sign_agreement: float
    spearman: float
    small_flip_share: float  # Of the sign disagreements, the share where both shifts are small.


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


def build_share_axis(archetype_shares: np.ndarray, contrast_shares: np.ndarray) -> Axis | None:
    """The same axis over card shares, each card its own coordinate: each card's alignment is beta_c = (a_c - b_c) / |a - b|. None when the shares
    coincide."""
    difference = archetype_shares - contrast_shares
    gap = float(np.linalg.norm(difference))
    if gap == 0:
        return None
    direction = difference / gap
    return Axis(direction, gap, direction)


def build_shift(axis: Axis, deck_lines: np.ndarray, target_lines: np.ndarray, movement: float) -> Shift:
    """movement is how far D moved at all: |v_D - v_T| on a space's axis, |l_D - l_T| on the share axis."""
    raw = float((deck_lines - target_lines) @ axis.alignment)
    return Shift(raw, raw / axis.gap, abs(raw) / movement if movement > 0 else None)


def build_contributions(axis: Axis, cards: Sequence[str], deck_lines: np.ndarray, target_lines: np.ndarray, diff: DeckDiff) -> Contributions:
    """The shift card by card: the cards and the rescaling add up to it exactly. lines and the axis's alignment are in cards' order."""
    parts = (deck_lines - target_lines) * axis.alignment
    column = {card: i for i, card in enumerate(cards)}
    before, after = Counter[str](), Counter[str]()
    for line in diff.kept + diff.removed:
        before[line.card] += line.n
    for line in diff.kept + diff.added:
        after[line.card] += line.n
    changed = sorted({line.card for line in diff.removed + diff.added})
    listed = [CardContribution(card, before[card], after[card], float(parts[column[card]]) if card in column else 0.0)  # No column, no part.
              for card in changed]
    return Contributions(listed, float(parts.sum()) - sum(c.contribution for c in listed))


def build_net_shift(space: DeckSpace, deck_lines: np.ndarray, deck_length: float, target_lines: np.ndarray, target_length: float) -> float:
    """lines are scaled and lengths are the decks' lengths before scaling (space.build_placed_decks), so lines x length is a deck's unscaled lines."""
    difference = space.vector(deck_lines * deck_length - target_lines * target_length)
    return float(np.linalg.norm(difference)) / ((deck_length + target_length) / 2)


def build_agreement(first: Sequence[float | None], second: Sequence[float | None], small: float = 0.05) -> Agreement:
    """Two shift fractions over the same pairs, skipping a pair where either is missing."""
    both = [(a, b) for a, b in zip(first, second, strict=True) if a is not None and b is not None]
    x, y = np.array([a for a, _ in both]), np.array([b for _, b in both])
    flips = np.sign(x) != np.sign(y)
    small_flips = flips & (np.abs(x) < small) & (np.abs(y) < small)
    return Agreement(len(both), float(1 - flips.mean()), float(stats.spearmanr(x, y).statistic), float(small_flips.sum() / flips.sum()))
