"""Which training rows a deck is diffed against (#62; 20261024_Deck_Diffs_Architecture.pdf): the models' matches, typical lists, and coverage draws by
how the two labels are related.
"""
from collections.abc import Set
from enum import Enum

import numpy as np

from archetype_classifier.evaluation.metrics import ArchetypeTree
from archetype_classifier.models.embedding_nearest import TrainingRows, build_candidates

NEAR_RIVALS = 5


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


def build_near_rivals(similarities: np.ndarray, rows: TrainingRows, label_id: int, count: int = NEAR_RIVALS) -> list[int]:
    """The best row of each of the count best-scoring other archetypes, ranked as the nearest deck ranks its candidates. An identical list under
    another label counts: it's the nearest rival there is. Of a label's tied best rows, the first."""
    rivals = [c.archetype_id for c in build_candidates(similarities, rows) if c.archetype_id != label_id][:count]
    return [int(np.flatnonzero(rows.labels == rival)[np.argmax(similarities[rows.labels == rival])]) for rival in rivals]


DRAWN = (PairClass.SAME, PairClass.SIBLING, PairClass.SAME_BRANCH, PairClass.UNRELATED, PairClass.ANCESTOR_DESCENDANT)

def build_coverage_rows(anchor_label: int, anchor_row: int | None, rows: TrainingRows, tree: ArchetypeTree, eligible: Set[int],
                        rng: np.random.Generator) -> dict[PairClass, int | None]:
    """One row per drawn class: a label uniformly among the eligible labels in the class, so large archetypes don't dominate it, then a row uniformly
    within the label. Never the anchor's own row (None for a deck that isn't a training row); None for a class with nothing to draw."""
    # Each label's rows are one run of rows.label_order, in row order, so no label's rows are searched for.
    ends = np.r_[rows.label_starts[1:], len(rows.label_order)]
    runs = {int(rows.labels[rows.label_order[start]]): (int(start), int(end)) for start, end in zip(rows.label_starts, ends, strict=True)}
    classes = {label: build_pair_class(tree, anchor_label, label) for label in sorted(eligible)}  # Eligible labels have rows.
    drawn: dict[PairClass, int | None] = {}
    def size(label: int) -> int:  # Only the anchor's own label can hold its row.
        start, end = runs[label]
        return end - start - (label == anchor_label and anchor_row is not None)
    for pair_class in DRAWN:
        labels = [label for label, c in classes.items() if c == pair_class and size(label) > 0]
        if not labels:
            drawn[pair_class] = None
            continue
        found = [r for r in rows.label_order[slice(*runs[labels[rng.integers(len(labels))]])].tolist() if r != anchor_row]
        drawn[pair_class] = int(found[rng.integers(len(found))])
    return drawn
