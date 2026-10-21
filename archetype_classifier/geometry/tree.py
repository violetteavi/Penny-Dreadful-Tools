"""Archetype tree helpers for the geometry (#64): an archetype's subtree and its siblings."""
from archetype_classifier.evaluation.metrics import ArchetypeTree


def build_subtree(tree: ArchetypeTree, label_id: int) -> frozenset[int]:
    """The archetype and every archetype below it."""
    return frozenset(a for a in tree.archetypes if label_id in tree.lineage(a))


def build_siblings(tree: ArchetypeTree, label_id: int) -> frozenset[int]:
    """The other archetypes under the same parent, with their own children. A top-level archetype's siblings are the other top-level ones."""
    parent = tree.archetypes[label_id].parent_id
    return frozenset().union(*(build_subtree(tree, a.id) for a in tree.archetypes.values() if a.parent_id == parent and a.id != label_id))
