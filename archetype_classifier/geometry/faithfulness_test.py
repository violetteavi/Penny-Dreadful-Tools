"""How faithful a map is, and the tree order for heatmaps (Scenarios.md, "Archetype geometry")."""
import numpy as np

from archetype_classifier.data_loading.dataset import ArchetypeSnapshot
from archetype_classifier.evaluation.metrics import ArchetypeTree
from archetype_classifier.geometry.faithfulness import build_neighbours_kept, build_tree_order

# Scenario: neighbours kept measures how faithful a map is. Four rows at 0, 10, 30 and 90 degrees in one plane.

ROWS = np.array([[np.cos(np.radians(t)), np.sin(np.radians(t))] for t in (0, 10, 30, 90)])

def test_a_map_that_keeps_the_order_keeps_every_nearest_neighbour() -> None:
    assert build_neighbours_kept(ROWS, np.array([[0.0], [1.0], [3.0], [9.0]]), k=1) == 1.0

def test_a_map_that_swaps_the_first_and_last_keeps_a_quarter() -> None:
    assert build_neighbours_kept(ROWS, np.array([[9.0], [1.0], [3.0], [0.0]]), k=1) == 0.25  # Only 30 -> 10 survives.

def test_neighbours_kept_averages_over_k() -> None:
    kept = build_neighbours_kept(ROWS, np.array([[9.0], [1.0], [3.0], [0.0]]), k=2)
    # By cosine, the two nearest: 0 -> {10, 30}, 10 -> {0, 30}, 30 -> {10, 0}, 90 -> {30, 10}. On the map: 0 -> {30, 10}, 10 -> {90, 30}, 30 -> {10, 90}, 90 -> {10, 30}.
    assert kept == (2 / 2 + 1 / 2 + 1 / 2 + 2 / 2) / 4


# The heatmaps' order: the tree, depth first, children by name.

def test_the_tree_order_is_depth_first_with_children_by_name() -> None:
    control, aggro, izzet, azorius, red, swarm = 1001, 1002, 65, 49, 16, 164
    tree = ArchetypeTree({control: ArchetypeSnapshot(control, 'Control', None, 0), aggro: ArchetypeSnapshot(aggro, 'Aggro', None, 0),
                          izzet: ArchetypeSnapshot(izzet, 'Izzet Control', control, 1), azorius: ArchetypeSnapshot(azorius, 'Azorius Control', control, 1),
                          red: ArchetypeSnapshot(red, 'Red Deck Wins', aggro, 1), swarm: ArchetypeSnapshot(swarm, 'Mono Red Swarm', aggro, 1)})
    assert build_tree_order(tree, [izzet, red, control, swarm, azorius]) == [swarm, red, control, azorius, izzet]  # Aggro itself has no centroid here.
