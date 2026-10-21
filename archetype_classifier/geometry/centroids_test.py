"""Centroids, typical lists and cohesion (Scenarios.md, "Archetype geometry")."""
import numpy as np
from scipy import sparse

from archetype_classifier.geometry.centroids import build_centroids, build_medoids, build_spread
from archetype_classifier.geometry.space import DeckSpace, build_space
from archetype_classifier.geometry.space_test import rows_space

MONO_BLACK_MIDRANGE, ORZHOV_CONTROL = 282, 512


# Scenario: the typical list is the row nearest the centroid.

def test_the_typical_list_is_the_row_nearest_the_centroid() -> None:
    space = rows_space([(MONO_BLACK_MIDRANGE, (1, 0, 0)), (MONO_BLACK_MIDRANGE, (0.6, 0.8, 0)), (MONO_BLACK_MIDRANGE, (0.8, 0.6, 0))])
    centroids = build_centroids(space, min_rows=1)
    assert np.allclose(space.matrix @ centroids.unit[0], [0.8638, 0.9214, 0.9933], atol=5e-5)
    assert build_medoids(space, centroids) == {MONO_BLACK_MIDRANGE: 2}

def test_a_list_submitted_many_times_can_become_the_typical_list() -> None:
    space = rows_space([(MONO_BLACK_MIDRANGE, (1, 0, 0), 4), (MONO_BLACK_MIDRANGE, (0.6, 0.8, 0)), (MONO_BLACK_MIDRANGE, (0.8, 0.6, 0))])
    centroids = build_centroids(space, min_rows=1)
    assert np.allclose(space.matrix @ centroids.unit[0], [0.9680, 0.7816, 0.9250], atol=5e-5)
    assert build_medoids(space, centroids) == {MONO_BLACK_MIDRANGE: 0}

def test_the_typical_list_also_has_the_highest_average_cosine_to_the_archetypes_decks() -> None:
    for counts, expected in (((1, 1, 1), [0.8000, 0.8533, 0.9200]), ((4, 1, 1), [0.9000, 0.7267, 0.8600])):
        vectors = [(1, 0, 0), (0.6, 0.8, 0), (0.8, 0.6, 0)]
        space = rows_space([(MONO_BLACK_MIDRANGE, v, n) for v, n in zip(vectors, counts, strict=True)])
        x, w = space.matrix, space.rows.deck_counts
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


# Scenario: cohesion measures how tightly an archetype's lists point the same way.

def test_cohesion_is_one_for_identical_lists() -> None:
    centroids = build_centroids(rows_space([(ORZHOV_CONTROL, (1, 0, 0)), (ORZHOV_CONTROL, (1, 0, 0))]), min_rows=1)
    assert np.isclose(centroids.cohesion[0], 1.0)

def test_cohesion_of_two_orthogonal_lists_is_the_root_of_a_half() -> None:
    centroids = build_centroids(rows_space([(ORZHOV_CONTROL, (1, 0, 0)), (ORZHOV_CONTROL, (0, 1, 0))]), min_rows=1)
    assert np.isclose(centroids.cohesion[0], 0.7071, atol=5e-5)

def test_deck_counts_tilt_cohesion() -> None:
    centroids = build_centroids(rows_space([(ORZHOV_CONTROL, (1, 0, 0), 3), (ORZHOV_CONTROL, (0, 1, 0))]), min_rows=1)
    assert np.isclose(centroids.cohesion[0], 0.7906, atol=5e-5)
    assert np.isclose(centroids.cohesion[0] ** 2, (9 + 1) / 16)  # The mean cosine over the 16 pairs of decks, each with itself included.


# Ties between typical lists break as the nearest deck breaks them: the most decks, then the newest deck.

def test_a_tie_for_the_typical_list_goes_to_the_row_with_more_decks_then_the_newer_deck() -> None:
    more = rows_space([(ORZHOV_CONTROL, (1, 0, 0), 2), (ORZHOV_CONTROL, (1, 0, 0)), (ORZHOV_CONTROL, (0, 1, 0))])  # Two lists with the same vector tie exactly.
    assert build_medoids(more, build_centroids(more, min_rows=1))[ORZHOV_CONTROL] == 0  # More decks win, though row 1's deck is newer.
    newer = rows_space([(ORZHOV_CONTROL, (1, 0, 0), 2), (ORZHOV_CONTROL, (1, 0, 0), 2), (ORZHOV_CONTROL, (0, 1, 0))])
    assert build_medoids(newer, build_centroids(newer, min_rows=1))[ORZHOV_CONTROL] == 1  # Equal decks: the newer deck.


# The bag of cards keeps its rows sparse (#62): centroids and typical lists come out the same as from the same rows dense.

def as_sparse(space: DeckSpace) -> DeckSpace:
    return build_space(space.rows, sparse.csr_matrix(space.matrix), space.lines, space.cards, space.embedding)

def test_sparse_rows_give_the_same_centroids_and_typical_lists_as_dense_ones() -> None:
    dense = rows_space([(MONO_BLACK_MIDRANGE, (1, 0, 0), 3), (ORZHOV_CONTROL, (0, 1, 0)), (MONO_BLACK_MIDRANGE, (0.8, 0.6, 0)), (ORZHOV_CONTROL, (0, 0.6, 0.8), 2)])
    expected, actual = build_centroids(dense, min_rows=1), build_centroids(as_sparse(dense), min_rows=1)
    assert actual.label_ids.tolist() == expected.label_ids.tolist()
    assert np.allclose(actual.sums, expected.sums) and np.allclose(actual.unit, expected.unit)
    assert actual.weights.tolist() == expected.weights.tolist()
    assert np.allclose(actual.cohesion, expected.cohesion)
    assert build_medoids(as_sparse(dense), actual) == build_medoids(dense, expected)


# Spread (#62): 1 - the median cosine of an archetype's rows to its centroid, each row once.

def test_spread_is_one_minus_the_median_cosine_of_an_archetypes_rows_to_its_centroid() -> None:
    space = rows_space([(ORZHOV_CONTROL, (1, 0, 0)), (ORZHOV_CONTROL, (1, 0, 0)), (ORZHOV_CONTROL, (0, 1, 0)),  # Centroid along (2, 1, 0).
                        (MONO_BLACK_MIDRANGE, (0, 0, 1)), (MONO_BLACK_MIDRANGE, (0, 0, 1))])  # Identical lists.
    centroids = build_centroids(space, min_rows=1)
    assert centroids.label_ids.tolist() == [MONO_BLACK_MIDRANGE, ORZHOV_CONTROL]
    assert np.allclose(build_spread(space, centroids), [0, 1 - 2 / np.sqrt(5)])  # Orzhov Control's cosines: 2/sqrt(5) twice and 1/sqrt(5).

def test_a_list_submitted_many_times_counts_once_in_the_spread() -> None:
    space = rows_space([(ORZHOV_CONTROL, (1, 0, 0)), (ORZHOV_CONTROL, (1, 0, 0)), (ORZHOV_CONTROL, (0, 1, 0), 5)])  # Centroid along (2, 5, 0).
    spread = build_spread(space, build_centroids(space, min_rows=1))
    assert np.allclose(spread, [1 - 2 / np.sqrt(29)])  # The three rows' cosines are 2, 2 and 5 over sqrt(29): the median row is 2/sqrt(29), not the
                                                       # median deck's 5/sqrt(29), though five of the seven decks are the third list.
