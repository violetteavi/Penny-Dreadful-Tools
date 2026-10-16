"""Centroids, typical lists and cohesion (Scenarios.md, "Archetype geometry")."""
import numpy as np

from archetype_classifier.geometry.centroids import build_centroids, build_medoids
from archetype_classifier.geometry.space_test import rows_space

MONO_BLACK_MIDRANGE, ORZHOV_CONTROL = 282, 512


# Scenario: the typical list is the row nearest the centroid.

def test_the_typical_list_is_the_row_nearest_the_centroid() -> None:
    space = rows_space([(MONO_BLACK_MIDRANGE, (1, 0, 0)), (MONO_BLACK_MIDRANGE, (0.6, 0.8, 0)), (MONO_BLACK_MIDRANGE, (0.8, 0.6, 0))])
    centroids = build_centroids(space, min_rows=1)
    assert np.allclose(space.vectors.matrix @ centroids.unit[0], [0.8638, 0.9214, 0.9933], atol=5e-5)
    assert build_medoids(space, centroids) == {MONO_BLACK_MIDRANGE: 2}

def test_a_list_submitted_many_times_can_become_the_typical_list() -> None:
    space = rows_space([(MONO_BLACK_MIDRANGE, (1, 0, 0), 4), (MONO_BLACK_MIDRANGE, (0.6, 0.8, 0)), (MONO_BLACK_MIDRANGE, (0.8, 0.6, 0))])
    centroids = build_centroids(space, min_rows=1)
    assert np.allclose(space.vectors.matrix @ centroids.unit[0], [0.9680, 0.7816, 0.9250], atol=5e-5)
    assert build_medoids(space, centroids) == {MONO_BLACK_MIDRANGE: 0}

def test_the_typical_list_also_has_the_highest_average_cosine_to_the_archetypes_decks() -> None:
    for counts, expected in (((1, 1, 1), [0.8000, 0.8533, 0.9200]), ((4, 1, 1), [0.9000, 0.7267, 0.8600])):
        vectors = [(1, 0, 0), (0.6, 0.8, 0), (0.8, 0.6, 0)]
        space = rows_space([(MONO_BLACK_MIDRANGE, v, n) for v, n in zip(vectors, counts, strict=True)])
        x, w = space.vectors.matrix, space.rows.deck_counts
        average = (x @ x.T) @ w / w.sum()  # Each row's cosine to every deck of the archetype, its own included.
        assert np.allclose(average, expected, atol=5e-5)
        assert build_medoids(space, build_centroids(space, min_rows=1))[MONO_BLACK_MIDRANGE] == int(np.argmax(average))


# The floor: an archetype with too few rows gets no centroid, and is counted rather than raised.

def test_an_archetype_below_the_floor_gets_no_centroid_and_is_counted() -> None:
    space = rows_space([(MONO_BLACK_MIDRANGE, (1, 0, 0)), (ORZHOV_CONTROL, (0, 1, 0), 5), (MONO_BLACK_MIDRANGE, (0.8, 0.6, 0))])
    centroids = build_centroids(space, min_rows=2)
    assert centroids.label_ids.tolist() == [MONO_BLACK_MIDRANGE]
    assert centroids.skipped == {ORZHOV_CONTROL: 1}  # Rows, not decks: its one list was submitted 5 times.
    assert build_medoids(space, centroids) == {MONO_BLACK_MIDRANGE: 2}
