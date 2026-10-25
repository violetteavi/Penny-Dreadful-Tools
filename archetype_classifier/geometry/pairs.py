"""Which training rows a deck is diffed against (#62; 20261024_Deck_Diffs_Architecture.pdf): the models' matches, typical lists, and coverage draws by
how the two labels are related.
"""
import numpy as np

from archetype_classifier.models.embedding_nearest import TrainingRows


def build_match_row(rows: TrainingRows, match_deck_id: int, label_id: int) -> int:
    """The training row behind a stored guess: the row whose newest deck is the evidence's match_deck_id, under the guessed label. Refused when there's
    none, which would mean the guess came from another model's rows."""
    found = np.flatnonzero((rows.newest_deck_ids == match_deck_id) & (rows.labels == label_id))
    if not len(found):
        raise ValueError(f'No training row with newest deck {match_deck_id} under label {label_id}')
    return int(found[0])
