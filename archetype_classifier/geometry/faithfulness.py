"""How far to trust a picture of the space (#64; Scenarios.md, "Archetype geometry"), and the order its heatmaps follow.

Any two-dimensional map of thousands of rows distorts them (docs/research/visualising-deck-space.md), so the one illustrative map prints its
neighbours kept: the mean share of each row's k nearest neighbours by cosine in the space that are still among its k nearest by distance on the map.
"""
from collections.abc import Sequence

import numpy as np

from archetype_classifier.evaluation.metrics import ArchetypeTree

CHUNK = 500  # Rows whose neighbours are found at once: two 500 x 84,000 float64 blocks are about 670 MB.


def build_neighbours_kept(high: np.ndarray, low: np.ndarray, k: int = 10) -> float:
    """high: unit vectors, compared by cosine; low: the same rows' map positions, compared by distance. Exact, in chunks."""
    kept = 0.0
    for start in range(0, len(high), CHUNK):
        rows = np.arange(start, min(start + CHUNK, len(high)))
        similarity = high[rows] @ high.T
        distance = (low[rows] ** 2).sum(axis=1)[:, None] + (low ** 2).sum(axis=1)[None, :] - 2 * low[rows] @ low.T  # Squared, without a rows x n x 2 block.
        similarity[np.arange(len(rows)), rows] = -np.inf
        distance[np.arange(len(rows)), rows] = np.inf
        nearest_high = np.argsort(-similarity, axis=1, kind='stable')[:, :k]
        nearest_low = np.argsort(distance, axis=1, kind='stable')[:, :k]
        kept += sum(len(set(h) & set(lo)) / k for h, lo in zip(nearest_high.tolist(), nearest_low.tolist(), strict=True))
    return kept / len(high)


def build_tree_order(tree: ArchetypeTree, label_ids: Sequence[int]) -> list[int]:
    """The given archetypes in tree order: depth first, children by name. An archetype not given still leads the way to its children."""
    wanted = set(label_ids)
    children: dict[int | None, list[int]] = {}
    for a in sorted(tree.archetypes.values(), key=lambda a: a.name):
        children.setdefault(a.parent_id, []).append(a.id)
    order: list[int] = []
    def visit(parent: int | None) -> None:
        for child in children.get(parent, []):
            if child in wanted:
                order.append(child)
            visit(child)
    visit(None)
    return order
