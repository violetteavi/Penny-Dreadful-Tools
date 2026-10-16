"""The space a nearest-deck model reads decks in (#64): its training rows, their deck vectors, and the lines behind them.

It reuses what the model already builds: TrainingRows (lists, labels, deck counts, and the label grouping that centroids sum over) and DeckVectors
(the unit vectors and their scaled lines). For the embedding average the lines' columns are cards and E is the combined embedding, so the vectors are
lines @ E to rounding. For the bag of cards there's no E: the scaled bag is both the lines and the vectors.
"""
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from archetype_classifier.card_embeddings.deck_vectors import DeckVectors
from archetype_classifier.models.embedding_nearest import TrainingRows


@dataclass(frozen=True)
class DeckSpace:
    rows: TrainingRows
    vectors: DeckVectors  # One row per training row: the unit vectors in matrix, their scaled lines in lines.
    cards: tuple[str, ...]  # The columns of vectors.lines.
    embedding: np.ndarray | None  # E, one row per card; None when the lines are the vectors (the bag of cards).


def build_space(rows: TrainingRows, vectors: DeckVectors, cards: Sequence[str], embedding: np.ndarray | None) -> DeckSpace:
    """Refuses parts that don't fit together: a space with mismatched rows would put vectors under the wrong labels."""
    if len(vectors.matrix) != len(rows.labels):
        raise ValueError(f'The space has {len(rows.labels)} rows but {len(vectors.matrix)} vectors')
    if vectors.lines.shape[1] != len(cards):
        raise ValueError(f'The lines have {vectors.lines.shape[1]} columns but {len(cards)} cards')
    if embedding is not None and len(embedding) != len(cards):
        raise ValueError(f'The space has {len(cards)} cards but the embedding has {len(embedding)} rows')
    return DeckSpace(rows, vectors, tuple(cards), embedding)
