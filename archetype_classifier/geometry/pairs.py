"""Which training rows a deck is diffed against (#62; 20261024_Deck_Diffs_Architecture.pdf): the models' matches, typical lists, and coverage draws by
how the two labels are related.
"""
from enum import Enum

import numpy as np

from archetype_classifier.evaluation.metrics import ArchetypeTree
from archetype_classifier.models.embedding_nearest import TrainingRows


class PairClass(Enum):
    SAME = 'same'
    SIBLING = 'sibling'  # The same parent, which isn't the root.
    SAME_BRANCH = 'same branch'  # The same top-level archetype, otherwise.
    UNRELATED = 'unrelated'  # Another top-level archetype.
    ANCESTOR_DESCENDANT = 'ancestor/descendant'  # One label is in the other's lineage.
    NEAR_RIVAL = 'near rival'  # The best row of one of the best-scoring other archetypes (build_near_rivals), whatever the relation.


def build_match_row(rows: TrainingRows, match_deck_id: int, label_id: int) -> int:
    """The training row behind a stored guess: the row whose newest deck is the evidence's match_deck_id, under the guessed label. Refused when there's
    none, which would mean the guess came from another model's rows."""
    found = np.flatnonzero((rows.newest_deck_ids == match_deck_id) & (rows.labels == label_id))
    if not len(found):
        raise ValueError(f'No training row with newest deck {match_deck_id} under label {label_id}')
    return int(found[0])


def build_pair_class(tree: ArchetypeTree, deck_label: int, row_label: int) -> PairClass:
    """Exactly one class for two labels, ancestor/descendant first."""
    if deck_label == row_label:
        return PairClass.SAME
    deck_lineage, row_lineage = tree.lineage(deck_label), tree.lineage(row_label)
    if deck_label in row_lineage or row_label in deck_lineage:
        return PairClass.ANCESTOR_DESCENDANT
    parent = tree.archetypes[deck_label].parent_id
    if parent is not None and parent == tree.archetypes[row_label].parent_id:
        return PairClass.SIBLING
    return PairClass.SAME_BRANCH if deck_lineage & row_lineage else PairClass.UNRELATED
