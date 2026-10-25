"""Card specificity (#62): how specific a card is on its own, whatever archetype it's in. Its IDF is its card weight (models.card_weights); its label
concentration is the share of the training rows playing it that carry its most common label (#64's definition). Each row counts once whatever its
deck count, under exact labels: a parent and its child are different labels.
"""
import numpy as np
from scipy import sparse

from archetype_classifier.geometry.space import Presence


def build_label_concentration(presence: Presence, labels: np.ndarray) -> np.ndarray:
    """In presence.cards order; labels are the rows' labels, in presence's row order."""
    distinct, row_label = np.unique(labels, return_inverse=True)
    indicator = sparse.csr_matrix((np.ones(len(labels)), (row_label, np.arange(len(labels)))), shape=(len(distinct), len(labels)))
    by_label = (indicator @ presence.matrix).toarray()  # Labels x cards: the rows with each label that play each card.
    return by_label.max(axis=0) / by_label.sum(axis=0)
