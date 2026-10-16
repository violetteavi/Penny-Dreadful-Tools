"""Defining cards (#64; Scenarios.md, "Archetype geometry"): the cards an archetype's rows play far more often than a contrast set's rows.

Each card is counted once per row that plays it, whatever its copies and the row's deck count. With k_a of the archetype's n_a rows and k_o of the
contrast set's n_o rows playing it:

    log-odds = ln((k_a + 1) / (n_a - k_a + 1)) - ln((k_o + 1) / (n_o - k_o + 1))
    z        = log-odds / sqrt(1/(k_a + 1) + 1/(n_a - k_a + 1) + 1/(k_o + 1) + 1/(n_o - k_o + 1))

Cards rank by z, so a card seen in few rows ranks low without a play-rate floor (Monroe, Colaresi & Quinn 2008); the log-odds shows how exclusive it is.
"""
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

import numpy as np
from scipy import sparse

from archetype_classifier.evaluation.metrics import ArchetypeTree
from archetype_classifier.geometry.space import DeckSpace

TOP = 5
type Contrast = Literal['all', 'siblings']


@dataclass(frozen=True)
class Presence:
    cards: tuple[str, ...]  # Every card a training row's maindeck plays, in name order.
    matrix: sparse.csr_matrix  # Rows x cards: 1 where the row plays the card, whatever its copies.

@dataclass(frozen=True)
class DefiningCard:
    card: str
    rows_in: int  # The archetype's rows that play it.
    rows_out: int  # The contrast set's rows that play it.
    log_odds: float
    z: float


def build_ranked_cards(cards: Sequence[str], k_a: np.ndarray, n_a: int, k_o: np.ndarray, n_o: int, top: int) -> list[DefiningCard]:
    """The top cards by z, then log-odds, then name. Only cards with log-odds above 0, more common in the archetype than outside it, are listed."""
    log_odds = np.log((k_a + 1) / (n_a - k_a + 1)) - np.log((k_o + 1) / (n_o - k_o + 1))
    z = log_odds / np.sqrt(1 / (k_a + 1) + 1 / (n_a - k_a + 1) + 1 / (k_o + 1) + 1 / (n_o - k_o + 1))
    listed = sorted(np.flatnonzero(log_odds > 0).tolist(), key=lambda c: (-z[c], -log_odds[c], cards[c]))
    return [DefiningCard(cards[c], int(k_a[c]), int(k_o[c]), float(log_odds[c]), float(z[c])) for c in listed[:top]]


def build_presence(space: DeckSpace) -> Presence:
    """From the rows' maindecks, so a card the embedding lacks still counts."""
    cards = tuple(sorted({line.card for maindeck in space.rows.maindecks for line in maindeck}))
    column = {card: i for i, card in enumerate(cards)}
    rows = [r for r, maindeck in enumerate(space.rows.maindecks) for _ in maindeck]
    cols = [column[line.card] for maindeck in space.rows.maindecks for line in maindeck]
    matrix = sparse.csr_matrix((np.ones(len(rows)), (rows, cols)), shape=(len(space.rows.maindecks), len(cards)))
    matrix.sum_duplicates()
    matrix.data[:] = 1
    return Presence(cards, matrix)


def build_subtree(tree: ArchetypeTree, label_id: int) -> frozenset[int]:
    """The archetype and every archetype below it."""
    return frozenset(a for a in tree.archetypes if label_id in tree.lineage(a))


def build_siblings(tree: ArchetypeTree, label_id: int) -> frozenset[int]:
    """The other archetypes under the same parent, with their own children. A top-level archetype's siblings are the other top-level ones."""
    parent = tree.archetypes[label_id].parent_id
    return frozenset().union(*(build_subtree(tree, a.id) for a in tree.archetypes.values() if a.parent_id == parent and a.id != label_id))


def build_contrast(space: DeckSpace, tree: ArchetypeTree, label_id: int, contrast: Contrast) -> np.ndarray:
    """Which rows the archetype is compared with: every other row, or its siblings' rows."""
    if contrast == 'all':
        return space.rows.labels != label_id
    return np.isin(space.rows.labels, list(build_siblings(tree, label_id)))


def build_defining_cards(presence: Presence, space: DeckSpace, tree: ArchetypeTree, label_id: int, contrast: Contrast, top: int = TOP) -> list[DefiningCard]:
    """An archetype's defining cards against a contrast set. With no contrast rows (an only child against its siblings) there's nothing to compare: []."""
    mine = space.rows.labels == label_id
    others = build_contrast(space, tree, label_id, contrast)
    if not others.any():
        return []
    k_a = np.asarray(presence.matrix[mine].sum(axis=0)).ravel()
    k_o = np.asarray(presence.matrix[others].sum(axis=0)).ravel()
    return build_ranked_cards(presence.cards, k_a, int(mine.sum()), k_o, int(others.sum()), top)
