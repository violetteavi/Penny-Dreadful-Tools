"""Archetype tree helpers (#64), and the small trees the other geometry tests use."""
from archetype_classifier.data_loading.dataset import ArchetypeSnapshot
from archetype_classifier.evaluation.metrics import ArchetypeTree
from archetype_classifier.geometry.tree import build_siblings, build_subtree

# Izzet Control and Azorius Control under Control; Red Deck Wins under Aggro.
CONTROL, AGGRO, IZZET_CONTROL, AZORIUS_CONTROL, RED_DECK_WINS = 1001, 1002, 65, 49, 16
TREE = ArchetypeTree({CONTROL: ArchetypeSnapshot(CONTROL, 'Control', None, 0), AGGRO: ArchetypeSnapshot(AGGRO, 'Aggro', None, 0),
                      IZZET_CONTROL: ArchetypeSnapshot(IZZET_CONTROL, 'Izzet Control', CONTROL, 1),
                      AZORIUS_CONTROL: ArchetypeSnapshot(AZORIUS_CONTROL, 'Azorius Control', CONTROL, 1),
                      RED_DECK_WINS: ArchetypeSnapshot(RED_DECK_WINS, 'Red Deck Wins', AGGRO, 1)})

# Siblings: the other archetypes under the same parent, with their own children.
IZZET_TWIN, ACTUAL_TWIN, COMBO = 549, 557, 1003
FAMILY_TREE = ArchetypeTree({**TREE.archetypes, COMBO: ArchetypeSnapshot(COMBO, 'Combo', None, 0),
                             ACTUAL_TWIN: ArchetypeSnapshot(ACTUAL_TWIN, 'Actual Twin', COMBO, 1),
                             IZZET_TWIN: ArchetypeSnapshot(IZZET_TWIN, 'Izzet Twin', ACTUAL_TWIN, 2)})


def test_a_siblings_children_count_among_the_siblings() -> None:
    assert build_siblings(FAMILY_TREE, COMBO) == {CONTROL, IZZET_CONTROL, AZORIUS_CONTROL, AGGRO, RED_DECK_WINS}  # Top-level: the other top-level subtrees.
    assert build_siblings(FAMILY_TREE, IZZET_CONTROL) == {AZORIUS_CONTROL}
    assert build_subtree(FAMILY_TREE, COMBO) == {COMBO, ACTUAL_TWIN, IZZET_TWIN}

def test_an_only_child_has_no_siblings() -> None:
    assert build_siblings(FAMILY_TREE, IZZET_TWIN) == frozenset()
