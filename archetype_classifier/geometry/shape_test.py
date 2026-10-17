"""Overlap, separation and where parent-labelled rows sit (Scenarios.md, "Archetype geometry")."""
from collections import Counter

import numpy as np

from archetype_classifier.data_loading.dataset import ArchetypeSnapshot
from archetype_classifier.evaluation.metrics import ArchetypeTree
from archetype_classifier.geometry.centroids import build_centroids
from archetype_classifier.geometry.shape import build_overlap, build_parent_positions, build_separation
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


# Scenario: where a parent-labelled row sits. Aristocrats is the parent of Orzhov Aristocrats and Rakdos Aristocrats; Red Deck Wins is outside the family.

AGGRO, AGGRO_COMBO, ARISTOCRATS, ORZHOV_ARISTOCRATS, RAKDOS_ARISTOCRATS, SOLEMNITY_ARISTOCRATS = 1002, 1004, 58, 60, 332, 643
TREE = ArchetypeTree({AGGRO: ArchetypeSnapshot(AGGRO, 'Aggro', None, 0), AGGRO_COMBO: ArchetypeSnapshot(AGGRO_COMBO, 'Aggro-Combo', None, 0),
                      RED_DECK_WINS: ArchetypeSnapshot(RED_DECK_WINS, 'Red Deck Wins', AGGRO, 1),
                      ARISTOCRATS: ArchetypeSnapshot(ARISTOCRATS, 'Aristocrats', AGGRO_COMBO, 1),
                      ORZHOV_ARISTOCRATS: ArchetypeSnapshot(ORZHOV_ARISTOCRATS, 'Orzhov Aristocrats', ARISTOCRATS, 2),
                      RAKDOS_ARISTOCRATS: ArchetypeSnapshot(RAKDOS_ARISTOCRATS, 'Rakdos Aristocrats', ARISTOCRATS, 2),
                      SOLEMNITY_ARISTOCRATS: ArchetypeSnapshot(SOLEMNITY_ARISTOCRATS, 'Solemnity Aristocrats', ORZHOV_ARISTOCRATS, 3)})
FAMILY_ROWS = [(ORZHOV_ARISTOCRATS, (1, 0, 0)), (RAKDOS_ARISTOCRATS, (0, 1, 0)), (RED_DECK_WINS, (0, 0, 1)),
               (ARISTOCRATS, (1, 1, 0.1)), (ARISTOCRATS, (1, 0.4, 0.3)), (ARISTOCRATS, (0.3, 0.3, 1))]

def test_where_parent_labelled_rows_sit() -> None:
    space = rows_space(FAMILY_ROWS)
    positions = build_parent_positions(space, build_centroids(space, min_rows=1), TREE)
    assert [(p.row, p.parent_id, p.position) for p in positions] == [(3, ARISTOCRATS, 'between children'), (4, ARISTOCRATS, 'one child'), (5, ARISTOCRATS, 'elsewhere')]
    assert [(p.nearest_id, round(p.nearest_cosine, 4)) for p in positions] == [(ORZHOV_ARISTOCRATS, 0.7053), (ORZHOV_ARISTOCRATS, 0.8944), (RED_DECK_WINS, 0.9206)]
    assert [(p.runner_up_id, round(p.runner_up_cosine, 4)) for p in positions] == [(RAKDOS_ARISTOCRATS, 0.7053), (RAKDOS_ARISTOCRATS, 0.3578), (ORZHOV_ARISTOCRATS, 0.2762)]
    assert [None if p.own_cosine is None else round(p.own_cosine, 4) for p in positions] == [0.8972, 0.9499, 0.7795]

def test_a_parent_below_the_floor_still_has_its_rows_placed_without_an_own_cosine() -> None:
    space = rows_space([*FAMILY_ROWS[:3], *((label, v) for label, v in FAMILY_ROWS[:3]), (ARISTOCRATS, (1, 1, 0.1))])  # Two rows each, one parent row.
    positions = build_parent_positions(space, build_centroids(space, min_rows=2), TREE)
    assert [(p.row, p.position, p.own_cosine) for p in positions] == [(6, 'between children', None)]

def test_a_grandchild_is_never_a_candidate() -> None:
    space = rows_space([*FAMILY_ROWS[:3], (SOLEMNITY_ARISTOCRATS, (1, 1, 0.1)), (ARISTOCRATS, (1, 1, 0.1))])
    positions = build_parent_positions(space, build_centroids(space, min_rows=1), TREE)
    assert [(p.position, p.nearest_id, p.runner_up_id) for p in positions] == [('between children', ORZHOV_ARISTOCRATS, RAKDOS_ARISTOCRATS)]

def test_a_parent_with_fewer_than_two_children_with_centroids_has_no_positions() -> None:
    space = rows_space([(ORZHOV_ARISTOCRATS, (1, 0, 0)), (RED_DECK_WINS, (0, 0, 1)), (ARISTOCRATS, (1, 1, 0.1))])
    assert build_parent_positions(space, build_centroids(space, min_rows=1), TREE) == []


# Separation: each archetype's nearest other centroid, and how close its siblings are compared with everything else.

def test_separation_names_the_nearest_other_centroid_and_compares_siblings_with_the_rest() -> None:
    space = rows_space([(ORZHOV_ARISTOCRATS, (1, 0, 0)), (RAKDOS_ARISTOCRATS, (0.6, 0.8, 0)), (RED_DECK_WINS, (0, 0, 1)), (ARISTOCRATS, (0.8, 0.6, 0))])
    separation = {s.label_id: s for s in build_separation(build_centroids(space, min_rows=1), TREE)}
    orzhov = separation[ORZHOV_ARISTOCRATS]
    assert orzhov.nearest_cosine is not None and orzhov.sibling_mean is not None and orzhov.other_mean is not None
    assert (orzhov.nearest_id, round(orzhov.nearest_cosine, 4)) == (ARISTOCRATS, 0.8)  # Its parent, ahead of its sibling at 0.6.
    assert np.isclose(orzhov.sibling_mean, 0.6)  # Rakdos Aristocrats.
    assert np.isclose(orzhov.other_mean, (0.8 + 0) / 2)  # Aristocrats and Red Deck Wins.
    assert separation[RED_DECK_WINS].sibling_mean is None  # Aggro has no other child with a centroid.

def test_a_lone_archetype_has_no_nearest_other_centroid() -> None:
    separation = build_separation(build_centroids(rows_space([(RED_DECK_WINS, (0, 0, 1))]), min_rows=1), TREE)
    assert [(s.nearest_id, s.nearest_cosine, s.other_mean) for s in separation] == [(None, None, None)]
