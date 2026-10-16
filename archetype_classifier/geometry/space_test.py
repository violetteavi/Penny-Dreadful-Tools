"""The space a model reads decks in (#64), and helpers the other geometry tests build their spaces with."""
from collections import Counter
from collections.abc import Sequence

import numpy as np
import pytest
from scipy import sparse

from archetype_classifier.card_embeddings.deck_vectors import DeckVectors
from archetype_classifier.data_loading.dataset import CardCount, LabelStatus
from archetype_classifier.evaluation.model import PredictDeck, TrainingDeck
from archetype_classifier.geometry.space import DeckSpace, build_space
from archetype_classifier.models.embedding_nearest import build_training_rows

DIMENSIONS = ('dimension 1', 'dimension 2', 'dimension 3')


def unit(v: Sequence[float]) -> np.ndarray:
    a = np.asarray(v, dtype=np.float64)
    return a / np.linalg.norm(a)

def rows_space(rows: Sequence[tuple[int, Sequence[float]] | tuple[int, Sequence[float], int]]) -> DeckSpace:
    """A space given straight by its rows' deck vectors, as the rule-level scenarios give it: (label, vector) or (label, vector, decks), in row order.
    Each row is a distinct list (60 + i Islands, so only its identity matters), its vector is scaled to unit length, and there's no embedding:
    the lines are the vectors themselves, over three named dimensions."""
    training = []
    for i, (label, _, *decks) in enumerate(rows):
        for _ in range(decks[0] if decks else 1):
            deck = PredictDeck(len(training) + 1, 'League', (CardCount('Island', 60 + i),), ())
            training.append(TrainingDeck(deck, 30, label, True, LabelStatus.VERIFIED))
    matrix = np.array([unit(vector) for _, vector, *_ in rows])
    vectors = DeckVectors(matrix, np.full(len(rows), 60), np.zeros(len(rows), dtype=np.int64), Counter(), sparse.csr_matrix(matrix))
    return build_space(build_training_rows(training), vectors, DIMENSIONS, None)


def test_a_space_holds_the_rows_their_vectors_and_the_lines_columns() -> None:
    space = rows_space([(1, (1, 0, 0), 2), (2, (0, 3, 4))])
    assert space.rows.labels.tolist() == [1, 2]
    assert space.rows.deck_counts.tolist() == [2, 1]
    assert np.allclose(space.vectors.matrix, [[1, 0, 0], [0, 0.6, 0.8]])
    assert space.cards == DIMENSIONS
    assert space.embedding is None

def test_a_space_refuses_vectors_that_dont_match_its_rows() -> None:
    space = rows_space([(1, (1, 0, 0)), (2, (0, 1, 0))])
    with pytest.raises(ValueError, match='2 rows but 1 vectors'):
        build_space(space.rows, DeckVectors(space.vectors.matrix[:1], space.vectors.embedded[:1], space.vectors.skipped[:1], Counter(), space.vectors.lines[:1]),
                    DIMENSIONS, None)

def test_a_space_refuses_lines_that_dont_match_its_cards() -> None:
    space = rows_space([(1, (1, 0, 0))])
    with pytest.raises(ValueError, match='3 columns but 2 cards'):
        build_space(space.rows, space.vectors, DIMENSIONS[:2], None)

def test_a_space_refuses_an_embedding_that_doesnt_match_its_cards() -> None:
    space = rows_space([(1, (1, 0, 0))])
    with pytest.raises(ValueError, match='3 cards but the embedding has 2 rows'):
        build_space(space.rows, space.vectors, DIMENSIONS, np.eye(2, 3))
