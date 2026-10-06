import numpy as np
import pytest

from archetype_classifier.card_embeddings.combined import build_combined, build_standardisation
from archetype_classifier.card_embeddings.embeddings import Embeddings
from archetype_classifier.card_embeddings.neighbours import build_neighbours


def unit(*rows: list[float]) -> np.ndarray:
    matrix = np.array(rows, dtype=np.float32)
    return matrix / np.linalg.norm(matrix, axis=1, keepdims=True)

NAMES = ('Burst Lightning', 'Explosive Welcome', 'Lightning Strike', 'Shock')
TEXT = Embeddings(NAMES, unit([1, 0.1], [1, 0.3], [1, 0.2], [1, 0]), {'encoder': 'fake'})  # By text, all four are burn.
STRUCTURED = np.array([[1, 0], [8, 0], [2, 0], [1, 1]], dtype=np.float32)  # Mana value, and one more column.


# Standardising: each column to mean 0 and spread 1, with the statistics frozen when fitted.

def test_standardising_gives_each_column_mean_0_and_spread_1() -> None:
    standardised = build_standardisation(STRUCTURED).apply(STRUCTURED)
    assert standardised.mean(axis=0) == pytest.approx([0, 0], abs=1e-6)
    assert standardised.std(axis=0) == pytest.approx([1, 1], abs=1e-6)

def test_a_column_that_never_varies_standardises_to_zero() -> None:
    constant = np.array([[1, 5], [2, 5], [3, 5]], dtype=np.float32)
    assert build_standardisation(constant).apply(constant)[:, 1].tolist() == [0, 0, 0]

def test_new_cards_are_standardised_with_the_fitted_statistics_so_existing_rows_never_move() -> None:
    old, new = STRUCTURED[:3], STRUCTURED[3:]
    standardisation = build_standardisation(old)
    assert np.array_equal(standardisation.apply(np.concatenate([old, new]))[:3], standardisation.apply(old))


# Combining: alpha times the text cosine plus (1 - alpha) times the structured cosine.

def cosine(e: Embeddings, a: str, b: str) -> float:
    return float(e.matrix[e.names.index(a)] @ e.matrix[e.names.index(b)])

def test_alpha_1_is_the_text_embedding_alone() -> None:
    combined = build_combined(TEXT, STRUCTURED, 1.0)
    assert all(build_neighbours(combined, n, 3) == build_neighbours(TEXT, n, 3) for n in NAMES)

def test_alpha_0_is_the_structured_vector_alone() -> None:
    combined = build_combined(TEXT, STRUCTURED, 0.0)
    structured = Embeddings(NAMES, STRUCTURED / np.linalg.norm(STRUCTURED, axis=1, keepdims=True), {})
    assert all([x.name for x in build_neighbours(combined, n, 3)] == [x.name for x in build_neighbours(structured, n, 3)] for n in NAMES)

def test_the_combined_cosine_is_the_weighted_sum_of_the_two_cosines_and_rows_stay_unit_length() -> None:
    combined = build_combined(TEXT, STRUCTURED, 0.6)
    structured = Embeddings(NAMES, STRUCTURED / np.linalg.norm(STRUCTURED, axis=1, keepdims=True), {})
    for a, b in (('Shock', 'Lightning Strike'), ('Shock', 'Explosive Welcome')):
        assert cosine(combined, a, b) == pytest.approx(0.6 * cosine(TEXT, a, b) + 0.4 * cosine(structured, a, b), abs=1e-6)
    assert np.linalg.norm(combined.matrix, axis=1) == pytest.approx(np.ones(4), abs=1e-6)

def test_the_manifest_records_alpha_and_the_structured_scheme() -> None:
    assert build_combined(TEXT, STRUCTURED, 0.4, 'log').manifest == {'encoder': 'fake', 'alpha': 0.4, 'structured': 'log'}

def test_a_card_with_an_all_zero_structured_row_keeps_only_its_text() -> None:
    zeros = np.zeros_like(STRUCTURED)
    assert np.allclose(build_combined(TEXT, zeros, 0.5).matrix[:, :2], np.sqrt(0.5) * TEXT.matrix)

def test_structured_rows_must_match_the_text_rows() -> None:
    with pytest.raises(ValueError, match='4 cards of text but 3 structured rows'):
        build_combined(TEXT, STRUCTURED[:3], 0.5)
