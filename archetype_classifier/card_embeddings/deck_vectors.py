"""Deck vectors: a deck's maindeck as the average of its cards' combined embedding rows, weighted by copies, at unit length (#44).

Basic lands count like any other card. Only maindecks reach this module, so a sideboard never changes a deck's vector. A card the embedding lacks is
skipped and counted, never fatal.
"""
from collections import Counter
from collections.abc import Sequence
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


def build_deck_vectors(maindecks: Sequence[tuple[CardCount, ...]], embedding: CombinedEmbedding) -> DeckVectors:
    index = {name: i for i, name in enumerate(embedding.names)}
    rows, cols, copies = [], [], []
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
                copies.append(line.n)
    counts = sparse.csr_matrix((copies, (rows, cols)), shape=(len(maindecks), len(index)), dtype=np.float64)
    summed = np.asarray(counts @ embedding.vectors.astype(np.float64))
    norms = np.linalg.norm(summed, axis=1, keepdims=True)
    matrix = np.divide(summed, norms, out=np.zeros_like(summed), where=norms > 0)
    return DeckVectors(matrix, np.asarray(counts.sum(axis=1), dtype=np.int64).ravel(), skipped, skipped_cards)
