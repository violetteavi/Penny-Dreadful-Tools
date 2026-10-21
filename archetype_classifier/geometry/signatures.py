"""What sets an archetype apart from a contrast, as ranked cards (#64, #62; Scenarios.md, "Archetype geometry"): defining cards and centroid pushes.

Defining cards are the cards an archetype's rows play far more often than a row contrast's rows.

Each card is counted once per row that plays it, whatever its copies and the row's deck count. With k_a of the archetype's n_a rows and k_o of the
contrast's n_o rows playing it:

    log-odds = ln((k_a + 1) / (n_a - k_a + 1)) - ln((k_o + 1) / (n_o - k_o + 1))
    z        = log-odds / sqrt(1/(k_a + 1) + 1/(n_a - k_a + 1) + 1/(k_o + 1) + 1/(n_o - k_o + 1))

Cards rank by z, so a card seen in few rows ranks low without a play-rate floor (Monroe, Colaresi & Quinn 2008); the log-odds shows how exclusive it is.

A centroid push is what the deck vectors themselves use to tell an archetype from its siblings. Each row's unit vector is its scaled lines times the
embedding, so an archetype's deck-weighted mean vector is mu_A = sum_c a_c e_c, with a_c the deck-weighted mean of card c's scaled line: how much of the
archetype's average is card c. With b_c the same over its siblings' rows and u the unit direction from mu_S to mu_A, card c pushes
(a_c - b_c)(e_c . u), and the pushes add up exactly to |mu_A - mu_S|.
"""
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from archetype_classifier.evaluation.metrics import ArchetypeTree
from archetype_classifier.geometry.centroids import mean_lines
from archetype_classifier.geometry.contrasts import RowContrast, build_contrast_rows
from archetype_classifier.geometry.space import DeckSpace, Presence

TOP = 5


@dataclass(frozen=True)
class CardPush:
    card: str
    share_in: float  # a_c: how much of the archetype's average is this card.
    share_out: float  # b_c: the same over its siblings' rows.
    alignment: float  # The card's embedding along the unit direction from the siblings' average to the archetype's.
    push: float  # (share_in - share_out) x alignment.

@dataclass(frozen=True)
class CentroidPush:
    distance: float  # |mu_A - mu_S|, which the pushes add up to.
    cards: list[CardPush]  # Every card either side plays, the largest push first.

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


def build_defining_cards(presence: Presence, space: DeckSpace, tree: ArchetypeTree, label_id: int, row_contrast: RowContrast, top: int = TOP) -> list[DefiningCard]:
    """An archetype's defining cards against a row contrast. With no contrast rows (an only child against its siblings) there's nothing to compare: []."""
    mine = space.rows.labels == label_id
    others = build_contrast_rows(space, tree, label_id, row_contrast)
    if not others.any():
        return []
    k_a = np.asarray(presence.matrix[mine].sum(axis=0)).ravel()
    k_o = np.asarray(presence.matrix[others].sum(axis=0)).ravel()
    return build_ranked_cards(presence.cards, k_a, int(mine.sum()), k_o, int(others.sum()), top)


def build_centroid_push(space: DeckSpace, tree: ArchetypeTree, label_id: int) -> CentroidPush | None:
    """Each card's push between the archetype and its siblings, or None when it has no siblings' rows to compare with. In the bag of cards (no
    embedding), a card's embedding is its own coordinate."""
    siblings = build_contrast_rows(space, tree, label_id, 'siblings')
    if not siblings.any():
        return None
    a, b = (mean_lines(space, rows) for rows in (space.rows.labels == label_id, siblings))
    embedding = space.embedding if space.embedding is not None else np.eye(len(space.cards))
    difference = (a - b) @ embedding
    distance = float(np.linalg.norm(difference))
    alignment = embedding @ (difference / distance) if distance > 0 else np.zeros(len(space.cards))
    played = np.flatnonzero((a != 0) | (b != 0)).tolist()
    pushes = [CardPush(space.cards[c], float(a[c]), float(b[c]), float(alignment[c]), float((a[c] - b[c]) * alignment[c])) for c in played]
    return CentroidPush(distance, sorted(pushes, key=lambda p: (-p.push, p.card)))
