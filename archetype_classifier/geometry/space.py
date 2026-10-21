"""The space a nearest-deck model reads decks in (#64, #62): its training rows, their deck vectors, and the lines behind them.

It reuses what the model already builds: TrainingRows (lists, labels, deck counts, and the label grouping that centroids sum over), and the unit
vectors with their scaled lines. For the embedding average the lines' columns are cards and E is the combined embedding, so the vectors are lines @ E
to rounding. For the bag of cards there's no E: the scaled bag is both the lines and the vectors.
"""
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from scipy import sparse

from archetype_classifier.evaluation.model import Model
from archetype_classifier.models.embedding_nearest import EmbeddingNearestDeck, TrainingRows


@dataclass(frozen=True)
class DeckSpace:
    rows: TrainingRows
    matrix: np.ndarray | sparse.csr_matrix  # One unit vector per training row: dense for the embedding average, sparse for the bag of cards.
    lines: sparse.csr_matrix  # Each row's scaled lines, one column per card.
    cards: tuple[str, ...]  # The columns of lines.
    embedding: np.ndarray | None  # E, one row per card; None when the lines are the vectors (the bag of cards).

    def vector(self, shares: np.ndarray) -> np.ndarray:
        """Card shares as a vector in the space: shares @ E, or the shares themselves in the bag of cards."""
        return shares if self.embedding is None else shares @ self.embedding

    def alignment(self, direction: np.ndarray) -> np.ndarray:
        """Each card's alignment with a unit direction in the space: E @ u, or u itself in the bag of cards, where each card is its own coordinate."""
        return direction if self.embedding is None else self.embedding @ direction

@dataclass(frozen=True)
class Presence:
    cards: tuple[str, ...]  # Every card a training row's maindeck plays, in name order.
    matrix: sparse.csr_matrix  # Rows x cards: 1 where the row plays the card, whatever its copies.


def build_space(rows: TrainingRows, matrix: np.ndarray | sparse.csr_matrix, lines: sparse.csr_matrix, cards: Sequence[str],
                embedding: np.ndarray | None) -> DeckSpace:
    """Refuses parts that don't fit together: a space with mismatched rows would put vectors under the wrong labels."""
    if matrix.shape[0] != len(rows.labels):
        raise ValueError(f'The space has {len(rows.labels)} rows but {matrix.shape[0]} vectors')
    if lines.shape[1] != len(cards):
        raise ValueError(f'The lines have {lines.shape[1]} columns but {len(cards)} cards')
    if embedding is not None and len(embedding) != len(cards):
        raise ValueError(f'The space has {len(cards)} cards but the embedding has {len(embedding)} rows')
    return DeckSpace(rows, matrix, lines, tuple(cards), embedding)


def build_model_space(model: Model) -> DeckSpace:
    """A fitted nearest deck's space: its training rows with the very vectors it ranks them by, rebuilt by its own code, with their lines. The bag
    of cards comes with its own pass (#64)."""
    if not isinstance(model, EmbeddingNearestDeck):
        raise ValueError(f'No space for the {model.name} model yet: only the embedding nearest deck')
    vectors = model.deck_vectors(model.rows.maindecks)
    return build_space(model.rows, vectors.matrix, vectors.lines, model.embedding.names, model.embedding.vectors.astype(np.float64))


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

