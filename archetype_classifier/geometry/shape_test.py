"""Overlap, separation and where parent-labelled rows sit (Scenarios.md, "Archetype geometry")."""
from collections import Counter

import numpy as np

from archetype_classifier.geometry.centroids import build_centroids
from archetype_classifier.geometry.shape import build_overlap
from archetype_classifier.geometry.space_test import rows_space

IZZET_CONTROL, AZORIUS_CONTROL, RED_DECK_WINS = 65, 49, 16


# Scenario: a row nearer another archetype's centroid counts as overlap.

CROWDED = rows_space([(IZZET_CONTROL, (1, 0, 0)), (IZZET_CONTROL, (0.98, 0.2, 0)), (IZZET_CONTROL, (0.6, 0.8, 0)),
                      (AZORIUS_CONTROL, (0, 1, 0)), (AZORIUS_CONTROL, (0.2, 0.98, 0)), (RED_DECK_WINS, (0, 0, 1)), (RED_DECK_WINS, (0, 0.2, 0.98))])

def test_a_row_nearer_another_archetypes_centroid_counts_as_overlap() -> None:
    centroids = build_centroids(CROWDED, min_rows=1)
    index = centroids.index()
    row = CROWDED.vectors.matrix[2]
    assert np.isclose(row @ centroids.unit[index[IZZET_CONTROL]], 0.8486, atol=5e-5)
    assert np.isclose(row @ centroids.unit[index[AZORIUS_CONTROL]], 0.8562, atol=5e-5)
    overlap = build_overlap(CROWDED, centroids)
    assert (overlap[IZZET_CONTROL].rows, overlap[IZZET_CONTROL].overlapping, overlap[IZZET_CONTROL].nearer) == (3, 1, Counter({AZORIUS_CONTROL: 1}))
    assert (overlap[AZORIUS_CONTROL].overlapping, overlap[RED_DECK_WINS].overlapping) == (0, 0)

def test_rows_of_an_archetype_without_a_centroid_are_left_out() -> None:
    space = rows_space([(IZZET_CONTROL, (1, 0, 0)), (IZZET_CONTROL, (0.6, 0.8, 0)), (AZORIUS_CONTROL, (0, 1, 0))])
    overlap = build_overlap(space, build_centroids(space, min_rows=2))
    assert set(overlap) == {IZZET_CONTROL}
    assert (overlap[IZZET_CONTROL].rows, overlap[IZZET_CONTROL].overlapping) == (2, 0)  # Azorius Control has no centroid to be nearer.
