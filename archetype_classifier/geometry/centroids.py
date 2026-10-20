"""Centroids, typical lists and cohesion (#64; Scenarios.md, "Archetype geometry").

An archetype's rows are the training rows labelled exactly with it, not its children's. Its centroid sums their unit vectors, each times its deck
count. Its typical list is its row nearest the centroid: for unit vectors that's also the row with the highest average cosine to the archetype's decks,
since a row's summed cosine to them is its cosine to the unscaled centroid times that centroid's length, the same for every row.
"""
from dataclasses import dataclass

import numpy as np

from archetype_classifier.geometry.space import DeckSpace
from archetype_classifier.models.embedding_nearest import TIE_TOLERANCE

MIN_ROWS = 10  # The fewest training rows an archetype needs for a centroid.


@dataclass(frozen=True)
class Centroids:
    label_ids: np.ndarray  # The archetypes with a centroid, in label order.
    sums: np.ndarray  # One unscaled centroid per archetype: the sum of its rows' unit vectors, each times its deck count.
    weights: np.ndarray  # Each archetype's decks.
    unit: np.ndarray  # The sums at unit length.
    skipped: dict[int, int]  # Archetype -> rows, for archetypes below the floor.

    @property
    def cohesion(self) -> np.ndarray:
        """How tightly each archetype's lists point the same way: 1 when they all do. It's the root of the mean cosine over every pair of its decks,
        each deck paired with itself included."""
        return np.linalg.norm(self.sums, axis=1) / self.weights

    def index(self) -> dict[int, int]:
        """Archetype -> its position in these arrays."""
        return {int(label): i for i, label in enumerate(self.label_ids)}


def build_centroids(space: DeckSpace, min_rows: int = MIN_ROWS) -> Centroids:
    rows = space.rows
    order, starts = rows.label_order, rows.label_starts
    labels = rows.labels[order[starts]]
    counts = np.diff(np.r_[starts, len(order)])
    weighted = space.vectors.matrix[order] * rows.deck_counts[order, None]
    sums = np.add.reduceat(weighted, starts) if len(starts) else np.zeros((0, space.vectors.matrix.shape[1]))
    weights = np.add.reduceat(rows.deck_counts[order], starts) if len(starts) else np.zeros(0, dtype=np.int64)
    kept = counts >= min_rows
    skipped = {int(label): int(n) for label, n in zip(labels[~kept], counts[~kept], strict=True)}
    sums, norms = sums[kept], np.linalg.norm(sums[kept], axis=1, keepdims=True)
    return Centroids(labels[kept], sums, weights[kept], np.divide(sums, norms, out=np.zeros_like(sums), where=norms > 0), skipped)


def build_medoids(space: DeckSpace, centroids: Centroids) -> dict[int, int]:
    """Archetype -> its typical list's row. Rows within TIE_TOLERANCE of the best tie, as in the nearest deck: the most decks, then the newest deck, wins."""
    rows = space.rows
    medoids = {}
    for i, label in enumerate(centroids.label_ids.tolist()):
        mine = np.flatnonzero(rows.labels == label)
        cosines = space.vectors.matrix[mine] @ centroids.unit[i]
        tied = mine[cosines >= cosines.max() - TIE_TOLERANCE]
        medoids[label] = int(max(tied, key=lambda r: (rows.deck_counts[r], rows.newest_deck_ids[r])))
    return medoids
