"""The nearest deck on the combined embedding (#44): the similarity baseline's "copy the label of the best match", with each deck read as its deck
vector instead of its shared cards.

Training decks are grouped into training rows, one per distinct maindeck and label, so a list submitted many times is one piece of evidence. A deck
copies the label of the training row with the highest cosine similarity. Rows within TIE_TOLERANCE of the best are tied: among them the label with the
most decks wins, then the label whose newest deck is most recent. There's no archetype tree and no threshold: the model always guesses, unless none of
the deck's cards is in the embedding.
"""
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from archetype_classifier.data_loading.dataset import CardCount
from archetype_classifier.evaluation.model import TrainingDeck


@dataclass(frozen=True)
class TrainingRows:
    maindecks: tuple[tuple[CardCount, ...], ...]
    labels: np.ndarray
    deck_counts: np.ndarray
    newest_deck_ids: np.ndarray


def build_training_rows(training: Sequence[TrainingDeck]) -> TrainingRows:
    """One row per distinct maindeck and label, in order of first appearance. A deck with no label is skipped."""
    rows: dict[tuple[tuple[CardCount, ...], int], list[int]] = {}  # (maindeck, label) -> [decks, newest deck id]
    for d in training:
        if d.archetype_id is None:
            continue
        row = rows.setdefault((d.deck.maindeck, d.archetype_id), [0, d.deck.deck_id])
        row[0] += 1
        row[1] = max(row[1], d.deck.deck_id)
    return TrainingRows(tuple(maindeck for maindeck, _ in rows), np.array([label for _, label in rows], dtype=np.int64),
                        np.array([n for n, _ in rows.values()], dtype=np.int64), np.array([newest for _, newest in rows.values()], dtype=np.int64))
