"""What an archetype is compared with (#62; 20261020_Diff_Geometry_Architecture.pdf).

A row contrast is a set of training rows: every other row, or the archetype's siblings' rows. Defining cards count them.
"""
from typing import Literal

import numpy as np

from archetype_classifier.evaluation.metrics import ArchetypeTree
from archetype_classifier.geometry.space import DeckSpace
from archetype_classifier.geometry.tree import build_siblings

type RowContrast = Literal['all', 'siblings']


def build_contrast_rows(space: DeckSpace, tree: ArchetypeTree, label_id: int, row_contrast: RowContrast) -> np.ndarray:
    """Which rows the archetype is compared with: every other row, or its siblings' rows."""
    if row_contrast == 'all':
        return space.rows.labels != label_id
    return np.isin(space.rows.labels, list(build_siblings(tree, label_id)))
