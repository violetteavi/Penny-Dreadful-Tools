"""Deck vectors: a deck's maindeck as the sum of its cards' combined embedding rows, each times copies(n) x the card's weight, at unit length (#44, #50).
The lines behind each vector are kept too, scaled by the same length, for the archetype geometry (#64).
With no weights and linear copies, the defaults, that's the copy-weighted average of #44.

Basic lands count like any other card. Only maindecks reach this module, so a sideboard never changes a deck's vector. A card the embedding lacks is
skipped and counted, never fatal.
"""
from collections import Counter
from collections.abc import Callable, Sequence
from dataclasses import dataclass

import numpy as np
from scipy import sparse

from archetype_classifier.card_embeddings.combined_embedding import CombinedEmbedding
from archetype_classifier.data_loading.dataset import CardCount


@dataclass(frozen=True)
class DeckVectors:
    matrix: np.ndarray  # One unit-length float64 row per deck; all zeros for a deck with no embedded card.
    embedded: np.ndarray  # Maindeck copies found in the embedding, per deck.
    skipped: np.ndarray  # Maindeck copies the embedding lacks, per deck.
    skipped_cards: Counter[str]  # Copies of each missing card, over all the decks.
    lines: sparse.csr_matrix  # Each line's copies(n) x weight over its deck's unscaled length, columns in the embedding's order: lines @ E matches matrix to rounding (#64).


def build_deck_vectors(maindecks: Sequence[tuple[CardCount, ...]], embedding: CombinedEmbedding, weight: Callable[[str], float] | None = None,
                       copies: Callable[[int], float] = float) -> DeckVectors:
    """Each line counts copies(n) x weight(card); weight None counts every card as 1. The embedded and skipped counts stay in copies."""
    index = {name: i for i, name in enumerate(embedding.names)}
    rows, cols, values = [], [], []
    embedded = np.zeros(len(maindecks), dtype=np.int64)
    skipped = np.zeros(len(maindecks), dtype=np.int64)
    skipped_cards: Counter[str] = Counter()
    for row, maindeck in enumerate(maindecks):
        for line in maindeck:
            col = index.get(line.card)
            if col is None:
                skipped[row] += line.n
                skipped_cards[line.card] += line.n
            else:
                rows.append(row)
                cols.append(col)
                values.append(copies(line.n) * (1.0 if weight is None else weight(line.card)))
                embedded[row] += line.n
    lines = sparse.csr_matrix((values, (rows, cols)), shape=(len(maindecks), len(index)), dtype=np.float64)
    summed = np.asarray(lines @ embedding.vectors.astype(np.float64))
    norms = np.linalg.norm(summed, axis=1, keepdims=True)
    matrix = np.divide(summed, norms, out=np.zeros_like(summed), where=norms > 0)  # Not lines @ E: rounding could flip a tie and change a stored run.
    scale = np.divide(1.0, norms[:, 0], out=np.zeros(len(maindecks)), where=norms[:, 0] > 0)
    return DeckVectors(matrix, embedded, skipped, skipped_cards, sparse.csr_matrix(sparse.diags(scale) @ lines))
