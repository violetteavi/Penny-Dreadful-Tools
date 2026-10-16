"""Where rows sit relative to the archetypes' centroids (#64; Scenarios.md, "Archetype geometry"): overlap, separation and parent-labelled rows.

Only archetypes with a centroid take part: a row of an archetype below the floor is left out, and nothing can be nearer to it.
"""
from collections import Counter
from dataclasses import dataclass

import numpy as np

from archetype_classifier.geometry.centroids import Centroids
from archetype_classifier.geometry.space import DeckSpace

CHUNK = 10_000  # Rows compared with every centroid at once.


@dataclass(frozen=True)
class Overlap:
    rows: int
    overlapping: int  # Rows whose nearest centroid isn't their own archetype's.
    nearer: Counter[int]  # Which archetypes' centroids those rows are nearest, and how many.


def build_overlap(space: DeckSpace, centroids: Centroids) -> dict[int, Overlap]:
    index = centroids.index()
    own = np.array([index.get(int(label), -1) for label in space.rows.labels])
    rows = np.flatnonzero(own >= 0)
    nearest = np.concatenate([np.argmax(space.vectors.matrix[rows[i:i + CHUNK]] @ centroids.unit.T, axis=1) for i in range(0, len(rows), CHUNK)] or [np.zeros(0, int)])
    overlap = {}
    for i, label in enumerate(centroids.label_ids.tolist()):
        mine = own[rows] == i
        elsewhere = nearest[mine][nearest[mine] != i]
        overlap[label] = Overlap(int(mine.sum()), len(elsewhere), Counter(int(centroids.label_ids[j]) for j in elsewhere))
    return overlap
