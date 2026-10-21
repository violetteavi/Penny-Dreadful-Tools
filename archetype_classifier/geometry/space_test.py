"""The space a model reads decks in (#64), and helpers the other geometry tests build their spaces with."""
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path

import numpy as np
import pytest
from scipy import sparse

from archetype_classifier.card_embeddings.combined_embedding import save_combined_embedding
from archetype_classifier.card_embeddings.deck_vectors import DeckVectors
from archetype_classifier.data_loading.dataset import CardCount, LabelStatus
from archetype_classifier.evaluation.model import PredictDeck, TrainingDeck
from archetype_classifier.geometry.space import DeckSpace, build_model_space, build_presence, build_space
from archetype_classifier.models.bag_nearest import BagNearestDeck
from archetype_classifier.models.embedding_nearest import build_training_rows
from archetype_classifier.models.embedding_nearest_test import EMBEDDING, weighted

DIMENSIONS = ('dimension 1', 'dimension 2', 'dimension 3')


def unit(v: Sequence[float]) -> np.ndarray:
    a = np.asarray(v, dtype=np.float64)
    return a / np.linalg.norm(a)

def rows_space(rows: Sequence[tuple[int, Sequence[float]] | tuple[int, Sequence[float], int]]) -> DeckSpace:
    """A space given straight by its rows' deck vectors, as the rule-level scenarios give it: (label, vector) or (label, vector, decks), in row order.
    Each row is a distinct list (60 + i Islands, so only its identity matters), its vector is scaled to unit length, and there's no embedding:
    the lines are the vectors themselves, over named dimensions."""
    training: list[TrainingDeck] = []
    for i, (label, _, *decks) in enumerate(rows):
        for _ in range(decks[0] if decks else 1):
            deck = PredictDeck(len(training) + 1, 'League', (CardCount('Island', 60 + i),), ())
            training.append(TrainingDeck(deck, 30, label, True, LabelStatus.VERIFIED))
    matrix = np.array([unit(vector) for _, vector, *_ in rows])
    vectors = DeckVectors(matrix, np.full(len(rows), 60), np.zeros(len(rows), dtype=np.int64), Counter(), sparse.csr_matrix(matrix))
    return build_space(build_training_rows(training), vectors, tuple(f'dimension {d + 1}' for d in range(matrix.shape[1])), None)


# A hand-made card embedding (Scenarios.md, "Centroid pushes add up to what separates an archetype from its siblings"), real cards legal in seasons 30 and 39.
CARD_EMBEDDING: dict[str, tuple[float, ...]] = {'Island': (1, 0, 0), 'Mountain': (0.8, 0, 0.6), 'Essence Scatter': (0, 1, 0), 'Negate': (0, 0.8, 0.6), 'Shock': (0, 0, 1)}

def lists_space(rows: Sequence[tuple[int, tuple[CardCount, ...]]], embedding: Mapping[str, Sequence[float]] = CARD_EMBEDDING) -> DeckSpace:
    """A space of real decklists, one deck each, with no card weights and linear copies (run 14's deck vectors) on a hand-made embedding."""
    cards = tuple(embedding)
    column = {card: i for i, card in enumerate(cards)}
    raw = np.zeros((len(rows), len(cards)))
    for r, (_, maindeck) in enumerate(rows):
        for line in maindeck:
            raw[r, column[line.card]] += line.n
    e = np.array([embedding[c] for c in cards], dtype=np.float64)
    norms = np.linalg.norm(raw @ e, axis=1, keepdims=True)
    lines = raw / norms
    training = [TrainingDeck(PredictDeck(i + 1, 'League', maindeck, ()), 30, label, True, LabelStatus.VERIFIED) for i, (label, maindeck) in enumerate(rows)]
    vectors = DeckVectors(lines @ e, raw.sum(axis=1).astype(np.int64), np.zeros(len(rows), dtype=np.int64), Counter(), sparse.csr_matrix(lines))
    return build_space(build_training_rows(training), vectors, cards, e)

def deck(**counts: int) -> tuple[CardCount, ...]:
    """Card names as keywords, underscores for spaces."""
    return tuple(sorted((CardCount(name.replace('_', ' '), n) for name, n in counts.items()), key=lambda c: c.card))


def test_a_space_holds_the_rows_their_vectors_and_the_lines_columns() -> None:
    space = rows_space([(1, (1, 0, 0), 2), (2, (0, 3, 4))])
    assert space.rows.labels.tolist() == [1, 2]
    assert space.rows.deck_counts.tolist() == [2, 1]
    assert np.allclose(space.vectors.matrix, np.array([[1, 0, 0], [0, 0.6, 0.8]]))
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


# A fitted model's space: its own training rows, read the way it reads them.

@pytest.fixture
def small_embedding(tmp_path: Path) -> Path:
    return save_combined_embedding(EMBEDDING, tmp_path)

def test_a_models_space_has_exactly_its_row_vectors(small_embedding: Path) -> None:
    model = weighted(small_embedding, weights='idf', copies='sqrt')  # Run 17's kind of model, on the small embedding.
    space = build_model_space(model)
    assert np.array_equal(space.vectors.matrix, model.row_vectors)
    assert space.rows is model.rows
    assert space.cards == tuple(model.embedding.names)
    assert space.embedding is not None and np.allclose(space.vectors.lines @ space.embedding, space.vectors.matrix)

def test_the_bag_of_cards_is_refused_until_its_own_pass() -> None:
    with pytest.raises(ValueError, match="bag of cards nearest deck"):
        build_model_space(BagNearestDeck({'copies': 'sqrt'}))

def test_presence_counts_a_card_once_per_row_whatever_its_copies() -> None:
    space = lists_space([(65, deck(Shock=4, Island=56)), (65, deck(Shock=1, Island=59))])
    presence = build_presence(space)
    assert presence.cards == ('Island', 'Shock')
    assert presence.matrix.toarray().tolist() == [[1, 1], [1, 1]]
