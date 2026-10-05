import numpy as np
import pytest

from archetype_classifier.card_embeddings.embeddings import Embeddings
from archetype_classifier.card_embeddings.neighbours import Neighbour, build_neighbours


def unit(*rows: list[float]) -> np.ndarray:
    matrix = np.array(rows, dtype=np.float32)
    return matrix / np.linalg.norm(matrix, axis=1, keepdims=True)

# Shock and Burst Lightning point the same way; Lightning Strike is close; Cancel and Counterspell are elsewhere, at the same angle from Shock.
EMBEDDINGS = Embeddings(('Burst Lightning', 'Cancel', 'Counterspell', 'Lightning Strike', 'Shock'),
                        unit([1, 0, 0], [0, 1, 0], [0, 0, 1], [3, 1, 0], [1, 0, 0]), {})


def test_the_nearest_cards_come_first_with_their_cosine_similarity_and_the_card_itself_left_out() -> None:
    assert build_neighbours(EMBEDDINGS, 'Shock', 2) == [Neighbour('Burst Lightning', pytest.approx(1.0)), Neighbour('Lightning Strike', pytest.approx(3 / np.sqrt(10)))]

def test_ties_are_broken_by_name() -> None:
    assert [n.name for n in build_neighbours(EMBEDDINGS, 'Shock', 4)][2:] == ['Cancel', 'Counterspell']

def test_among_limits_the_cards_searched() -> None:
    assert [n.name for n in build_neighbours(EMBEDDINGS, 'Shock', 5, among={'Cancel', 'Lightning Strike', 'Shock'})] == ['Lightning Strike', 'Cancel']

def test_an_unknown_card_is_named_in_the_error() -> None:
    with pytest.raises(ValueError, match='Lightning Bolt is not in these embeddings'):
        build_neighbours(EMBEDDINGS, 'Lightning Bolt', 3)
