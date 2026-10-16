"""The space a nearest-deck model reads decks in (#64): its training rows, their deck vectors, and the lines behind them.

It reuses what the model already builds: TrainingRows (lists, labels, deck counts, and the label grouping that centroids sum over) and DeckVectors
(the unit vectors and their scaled lines). For the embedding average the lines' columns are cards and E is the combined embedding, so the vectors are
lines @ E to rounding. For the bag of cards there's no E: the scaled bag is both the lines and the vectors.
"""
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from archetype_classifier.card_embeddings.deck_vectors import DeckVectors
from archetype_classifier.evaluation.model import Model
from archetype_classifier.evaluation.store import load_model, load_run
from archetype_classifier.models.embedding_nearest import EmbeddingNearestDeck, TrainingRows
from shared.database import Database


@dataclass(frozen=True)
class DeckSpace:
    rows: TrainingRows
    vectors: DeckVectors  # One row per training row: the unit vectors in matrix, their scaled lines in lines.
    cards: tuple[str, ...]  # The columns of vectors.lines.
    embedding: np.ndarray | None  # E, one row per card; None when the lines are the vectors (the bag of cards).


def build_space(rows: TrainingRows, vectors: DeckVectors, cards: Sequence[str], embedding: np.ndarray | None) -> DeckSpace:
    """Refuses parts that don't fit together: a space with mismatched rows would put vectors under the wrong labels."""
    if len(vectors.matrix) != len(rows.labels):
        raise ValueError(f'The space has {len(rows.labels)} rows but {len(vectors.matrix)} vectors')
    if vectors.lines.shape[1] != len(cards):
        raise ValueError(f'The lines have {vectors.lines.shape[1]} columns but {len(cards)} cards')
    if embedding is not None and len(embedding) != len(cards):
        raise ValueError(f'The space has {len(cards)} cards but the embedding has {len(embedding)} rows')
    return DeckSpace(rows, vectors, tuple(cards), embedding)


def build_model_space(model: Model) -> DeckSpace:
    """A fitted nearest deck's space: its training rows with the very vectors it ranks them by, rebuilt by its own code, with their lines. The bag
    of cards comes with its own pass (#64)."""
    if not isinstance(model, EmbeddingNearestDeck):
        raise ValueError(f'No space for the {model.name} model yet: only the embedding nearest deck')
    vectors = model.deck_vectors(model.rows.maindecks)
    return build_space(model.rows, vectors, model.embedding.names, model.embedding.vectors.astype(np.float64))


def load_space(edb: Database, run_id: int) -> DeckSpace:
    """The space of a stored run's model, refitted from its record as store.load_model refits it."""
    _, model = load_model(edb, load_run(edb, run_id).model_id)
    return build_model_space(model)
