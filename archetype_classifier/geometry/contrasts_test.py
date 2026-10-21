"""What an archetype is compared with (#62): span neighbours and contrasts."""
import numpy as np

from archetype_classifier.geometry.analogies_test import centroids_at
from archetype_classifier.geometry.contrasts import (
    BlendRule,
    Neighbour,
    NeighbourContrast,
    build_blended_contrast,
    build_global_contrast,
    build_neighbour_contrasts,
    build_span_neighbours,
)

IZZET_TWIN, CONTROL, SLIVERS = 549, 1001, 1004

# A tight archetype (spread 0.01) inside a loose one's span (spread 0.15): their centroids are 0.1 apart (cosine 0.9). A third sits far from both.
TIGHT_INSIDE_LOOSE = centroids_at({IZZET_TWIN: (1, 0, 0), CONTROL: (0.9, np.sqrt(1 - 0.81), 0), SLIVERS: (0, 0, 1)})
SPREAD = np.array([0.01, 0.15, 0.05])  # In label order: Izzet Twin, Control, Slivers.


def test_a_tight_archetype_inside_a_loose_ones_span_is_its_neighbour_both_ways() -> None:
    neighbours = build_span_neighbours(TIGHT_INSIDE_LOOSE, SPREAD)
    assert [(n.label_id, n.inside_mine, n.inside_theirs) for n in neighbours[IZZET_TWIN]] == [(CONTROL, False, True)]  # ↑: Izzet Twin is inside Control's span.
    assert [(n.label_id, n.inside_mine, n.inside_theirs) for n in neighbours[CONTROL]] == [(IZZET_TWIN, True, False)]  # ↓: Izzet Twin is inside its span.
    assert np.isclose(neighbours[IZZET_TWIN][0].cosine, 0.9)

def test_an_archetype_outside_every_span_has_no_neighbours_but_still_a_key() -> None:
    neighbours = build_span_neighbours(TIGHT_INSIDE_LOOSE, SPREAD)
    assert neighbours[SLIVERS] == []
    assert set(neighbours) == {IZZET_TWIN, CONTROL, SLIVERS}

def test_the_width_scales_how_far_a_span_reaches() -> None:
    assert build_span_neighbours(TIGHT_INSIDE_LOOSE, SPREAD, width=0.5)[IZZET_TWIN] == []  # Control's span reaches 0.075, short of 0.1.
    assert [(n.inside_mine, n.inside_theirs) for n in build_span_neighbours(TIGHT_INSIDE_LOOSE, SPREAD, width=15)[IZZET_TWIN]] == [(True, True)]  # ↑↓: its own span reaches 0.15.


# Neighbours come nearest first, ties by label id.

AGGRO, HUMANS, GOBLINS, ELVES = 1002, 7, 8, 9

def test_neighbours_come_nearest_first_with_ties_by_label() -> None:
    centroids = centroids_at({AGGRO: (1, 0, 0), GOBLINS: (0.8, 0.6, 0), HUMANS: (0.8, -0.6, 0), ELVES: (0.9, 0, np.sqrt(1 - 0.81))})
    spread = np.array([0.01, 0.01, 0.01, 0.5])  # Label order: Humans, Goblins, Elves, Aggro. Only Aggro is loose.
    assert [n.label_id for n in build_span_neighbours(centroids, spread)[AGGRO]] == [ELVES, HUMANS, GOBLINS]  # Humans and Goblins tie at 0.8.

def test_being_neighbours_is_symmetric() -> None:
    centroids = centroids_at({AGGRO: (1, 0, 0), GOBLINS: (0.8, 0.6, 0), HUMANS: (0.8, -0.6, 0), ELVES: (0.9, 0, np.sqrt(1 - 0.81))})
    neighbours = build_span_neighbours(centroids, np.array([0.3, 0.05, 0.12, 0.2]))
    pairs = {(label, n.label_id) for label, found in neighbours.items() for n in found}
    assert pairs and pairs == {(b, a) for a, b in pairs}
    mirrored = {(label, n.label_id): n for label, found in neighbours.items() for n in found}
    assert all(mirrored[(a, b)].inside_mine == mirrored[(b, a)].inside_theirs for a, b in pairs)
    assert isinstance(next(iter(mirrored.values())), Neighbour)


# Contrasts as card shares: the neighbours' mean, the global centroid, and a blend of the two.

FOUR = centroids_at({HUMANS: (1, 0, 0), GOBLINS: (0, 1, 0), ELVES: (0, 0, 1), AGGRO: (0.6, 0.8, 0)})  # Label order: Humans, Goblins, Elves, Aggro.
SHARES = np.array([[1.0, 0, 0], [0, 1.0, 0], [0, 0, 1.0], [0.2, 0.8, 0]])  # Each archetype's card shares, in label order.
NEIGHBOURS = {AGGRO: [Neighbour(GOBLINS, 0.8, True, False), Neighbour(HUMANS, 0.6, True, False)],
              HUMANS: [Neighbour(AGGRO, 0.6, False, True)], GOBLINS: [Neighbour(AGGRO, 0.8, False, True)], ELVES: []}

def test_a_local_contrast_is_the_plain_mean_of_the_neighbours_shares() -> None:
    contrasts = build_neighbour_contrasts(FOUR, SHARES, NEIGHBOURS)
    aggro, humans = contrasts[AGGRO].local_contrast, contrasts[HUMANS].local_contrast
    assert aggro is not None and np.allclose(aggro, [0.5, 0.5, 0])  # Humans and Goblins, each counted once.
    assert contrasts[AGGRO].neighbour_count == 2
    assert humans is not None and np.allclose(humans, [0.2, 0.8, 0])
    assert contrasts[ELVES] == NeighbourContrast(None, 0)

def test_the_global_contrast_is_the_plain_mean_of_every_archetypes_shares() -> None:
    assert np.allclose(build_global_contrast(SHARES), [0.3, 0.45, 0.25])

def test_with_one_neighbour_the_blend_is_half_local_and_half_global() -> None:
    blended = build_blended_contrast(build_neighbour_contrasts(FOUR, SHARES, NEIGHBOURS)[HUMANS], build_global_contrast(SHARES))
    assert np.allclose(blended, [0.25, 0.625, 0.125])  # (0.2, 0.8, 0) / 2 + (0.3, 0.45, 0.25) / 2.

def test_with_three_neighbours_the_global_contrast_counts_a_quarter() -> None:
    blended = build_blended_contrast(NeighbourContrast(np.array([1.0, 0]), 3), np.array([0, 1.0]), BlendRule.GLOBAL_AS_ONE_NEIGHBOUR)
    assert np.allclose(blended, [0.75, 0.25])

def test_with_no_neighbour_the_blend_is_the_global_contrast() -> None:
    assert np.allclose(build_blended_contrast(NeighbourContrast(None, 0), np.array([0.3, 0.7])), [0.3, 0.7])
