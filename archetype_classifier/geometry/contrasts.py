"""What an archetype is compared with (#62; 20261020_Diff_Geometry_Architecture.pdf).

A row contrast is a set of training rows: every other row, or the archetype's siblings' rows. Defining cards count them.

Span neighbours: an archetype's spread is 1 - the median cosine of its rows to its centroid (centroids.build_spread). Two archetypes are neighbours
when the gap between their centroids, 1 - cosine, is within width x the larger of their two spreads: one's span reaches the other's centroid. So a
tight archetype inside a loose, generic one's span is compared with it, and the loose one with it. There's no cap on how many.
"""
from dataclasses import dataclass
from typing import Literal

import numpy as np

from archetype_classifier.evaluation.metrics import ArchetypeTree
from archetype_classifier.geometry.centroids import Centroids
from archetype_classifier.geometry.space import DeckSpace
from archetype_classifier.geometry.tree import build_siblings

type RowContrast = Literal['all', 'siblings']


@dataclass(frozen=True)
class Neighbour:
    label_id: int
    cosine: float  # Between the two centroids.
    inside_mine: bool  # Its centroid is within width x my spread (↓: usually more specific than me).
    inside_theirs: bool  # Mine is within width x its spread (↑: usually a more generic archetype that contains me).


def build_contrast_rows(space: DeckSpace, tree: ArchetypeTree, label_id: int, row_contrast: RowContrast) -> np.ndarray:
    """Which rows the archetype is compared with: every other row, or its siblings' rows."""
    if row_contrast == 'all':
        return space.rows.labels != label_id
    return np.isin(space.rows.labels, list(build_siblings(tree, label_id)))


def build_span_neighbours(centroids: Centroids, spread: np.ndarray, width: float = 1.0) -> dict[int, list[Neighbour]]:
    """Every archetype with a centroid -> its neighbours, nearest first, ties by label id; an empty list when no span reaches. spread is in label
    order (centroids.build_spread). Each pair's cosine is read once and the pair added to both lists, so being neighbours is symmetric."""
    labels = centroids.label_ids.tolist()
    gaps = 1 - centroids.unit @ centroids.unit.T
    neighbours: dict[int, list[Neighbour]] = {label: [] for label in labels}
    for i, j in zip(*np.nonzero(np.triu(gaps <= width * np.maximum.outer(spread, spread), k=1)), strict=True):
        gap = float(gaps[i, j])
        mine, theirs = gap <= width * spread[i], gap <= width * spread[j]
        neighbours[labels[i]].append(Neighbour(labels[j], 1 - gap, bool(mine), bool(theirs)))
        neighbours[labels[j]].append(Neighbour(labels[i], 1 - gap, bool(theirs), bool(mine)))
    return {label: sorted(found, key=lambda n: (-n.cosine, n.label_id)) for label, found in neighbours.items()}
