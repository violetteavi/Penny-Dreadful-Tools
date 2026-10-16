"""Where rows sit relative to the archetypes' centroids (#64; Scenarios.md, "Archetype geometry"): overlap, separation and parent-labelled rows.

Only archetypes with a centroid take part: a row of an archetype below the floor is left out, and nothing can be nearer to it.
"""
from collections import Counter
from dataclasses import dataclass
from typing import Literal

import numpy as np

from archetype_classifier.evaluation.metrics import ArchetypeTree
from archetype_classifier.geometry.centroids import Centroids
from archetype_classifier.geometry.defining import build_subtree
from archetype_classifier.geometry.space import DeckSpace

CHUNK = 10_000  # Rows compared with every centroid at once.
MARGIN = 0.02  # Two children this close are a near-tie (#14: misses are near-ties within 0.02). A starting value, to revisit on the data.
type Position = Literal['between children', 'one child', 'elsewhere']


@dataclass(frozen=True)
class Overlap:
    rows: int
    overlapping: int  # Rows whose nearest centroid isn't their own archetype's.
    nearer: Counter[int]  # Which archetypes' centroids those rows are nearest, and how many.


@dataclass(frozen=True)
class ParentPosition:
    row: int
    parent_id: int  # The row's label.
    position: Position
    nearest_id: int
    nearest_cosine: float
    runner_up_id: int
    runner_up_cosine: float
    own_cosine: float | None  # To the parent's own centroid, reported but never a candidate; None when the parent has none.


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


def build_parent_positions(space: DeckSpace, centroids: Centroids, tree: ArchetypeTree, margin: float = MARGIN) -> list[ParentPosition]:
    """Where each row labelled at a parent with at least 2 children that have centroids sits, in row order. The candidates are those children and
    every archetype with a centroid outside the parent's subtree. The parent's own centroid isn't one: it's built from these very rows, so it would
    nearly always be nearest. Grandchildren are neither children nor outside, so they're left out.
    - between children: the two nearest candidates are children, within the margin;
    - one child: the nearest is a child, and the next isn't another child within the margin;
    - elsewhere: an archetype outside the family is nearest."""
    index = centroids.index()
    positions = []
    for parent in sorted({int(label) for label in space.rows.labels}):
        children = [label for label in centroids.label_ids.tolist() if tree.archetypes[label].parent_id == parent]
        if len(children) < 2:
            continue
        family = build_subtree(tree, parent)
        candidates = np.array([i for i, label in enumerate(centroids.label_ids.tolist()) if label in children or label not in family])
        is_child = np.isin(centroids.label_ids[candidates], children)
        for row in np.flatnonzero(space.rows.labels == parent).tolist():
            cosines = centroids.unit[candidates] @ space.vectors.matrix[row]
            first, second = np.argsort(-cosines, kind='stable')[:2]
            if not is_child[first]:
                position: Position = 'elsewhere'
            elif is_child[second] and cosines[first] - cosines[second] <= margin:
                position = 'between children'
            else:
                position = 'one child'
            positions.append(ParentPosition(row, parent, position, int(centroids.label_ids[candidates[first]]), float(cosines[first]),
                                            int(centroids.label_ids[candidates[second]]), float(cosines[second]),
                                            float(centroids.unit[index[parent]] @ space.vectors.matrix[row]) if parent in index else None))
    return positions
