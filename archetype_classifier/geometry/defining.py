"""Defining cards (#64; Scenarios.md, "Archetype geometry"): the cards an archetype's rows play far more often than a contrast set's rows.

Each card is counted once per row that plays it, whatever its copies and the row's deck count. With k_a of the archetype's n_a rows and k_o of the
contrast set's n_o rows playing it:

    log-odds = ln((k_a + 1) / (n_a - k_a + 1)) - ln((k_o + 1) / (n_o - k_o + 1))
    z        = log-odds / sqrt(1/(k_a + 1) + 1/(n_a - k_a + 1) + 1/(k_o + 1) + 1/(n_o - k_o + 1))

Cards rank by z, so a card seen in few rows ranks low without a play-rate floor (Monroe, Colaresi & Quinn 2008); the log-odds shows how exclusive it is.
"""
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np


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
    listed = sorted(np.flatnonzero(log_odds > 0), key=lambda c: (-z[c], -log_odds[c], cards[c]))
    return [DefiningCard(cards[c], int(k_a[c]), int(k_o[c]), float(log_odds[c]), float(z[c])) for c in listed[:top]]
