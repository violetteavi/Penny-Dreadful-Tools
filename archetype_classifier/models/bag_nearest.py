"""The nearest deck on the bag of cards (#50; Scenarios.md, "Deck representations"): each maindeck as a sparse vector with copies(n) x the card's
weight at each card it plays, compared by cosine. Two different cards never match, however alike their text.

The vocabulary is every card the training rows play. A card outside it has no column, but it still counts in the deck's own length: it lowers the
deck's cosine with every row by the same factor, so it can't change the ranking, and the scores stay true cosines.
"""
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

import numpy as np
from scipy import sparse

from archetype_classifier.data_loading.dataset import CardCount


@dataclass(frozen=True)
class BagVectors:
    matrix: sparse.csr_matrix  # One unit-length row per deck over the vocabulary; empty for a deck with no known card.
    known: np.ndarray  # Maindeck copies in the vocabulary, per deck.
    unseen: np.ndarray  # Maindeck copies outside it, per deck.


def build_vocabulary(maindecks: Sequence[tuple[CardCount, ...]]) -> dict[str, int]:
    """Every card the maindecks play, as a column, in name order."""
    return {card: i for i, card in enumerate(sorted({line.card for maindeck in maindecks for line in maindeck}))}

def build_bag_vectors(maindecks: Sequence[tuple[CardCount, ...]], vocabulary: Mapping[str, int], weight: Callable[[str], float],
                      copies: Callable[[int], float]) -> BagVectors:
    rows, cols, values = [], [], []
    known = np.zeros(len(maindecks), dtype=np.int64)
    unseen = np.zeros(len(maindecks), dtype=np.int64)
    norms = np.zeros(len(maindecks))
    for row, maindeck in enumerate(maindecks):
        for line in maindeck:
            value = copies(line.n) * weight(line.card)
            norms[row] += value * value
            col = vocabulary.get(line.card)
            if col is None:
                unseen[row] += line.n
            else:
                rows.append(row)
                cols.append(col)
                values.append(value)
                known[row] += line.n
    lengths = np.sqrt(norms)
    scaled = [v / lengths[r] for r, v in zip(rows, values, strict=True)]
    matrix = sparse.csr_matrix((scaled, (rows, cols)), shape=(len(maindecks), len(vocabulary)), dtype=np.float64)
    return BagVectors(matrix, known, unseen)
