"""Analogies (Scenarios.md, "Archetype geometry")."""
import numpy as np

from archetype_classifier.geometry.analogies import Analogy, build_analogy_scores, build_offset_scores
from archetype_classifier.geometry.centroids import Centroids, build_centroids
from archetype_classifier.geometry.space_test import rows_space

ORZHOV_MIDRANGE, ORZHOV_CONTROL, MONO_BLACK_MIDRANGE, MONO_BLACK_CONTROL, MONO_BLACK_AGGRO, MONO_BLACK_DEVOTION = 356, 512, 282, 18, 13, 324
CONTROL_RATHER_THAN_MIDRANGE = Analogy(ORZHOV_MIDRANGE, ORZHOV_CONTROL, MONO_BLACK_MIDRANGE, MONO_BLACK_CONTROL, 'strategy')

def centroids_at(points: dict[int, tuple[float, float, float]]) -> Centroids:
    """Each archetype one row, so its centroid is that row at unit length."""
    return build_centroids(rows_space([(label, v) for label, v in points.items()]), min_rows=1)

def score_of(centroids: Centroids, scores: np.ndarray, label: int) -> float:
    return float(scores[centroids.index()[label]])


# Scenario: a perfect parallelogram scores perfectly.

PARALLELOGRAM = centroids_at({ORZHOV_MIDRANGE: (0.8, 0, 0.6), ORZHOV_CONTROL: (0.8, 0, -0.6), MONO_BLACK_MIDRANGE: (-0.8, 0, 0.6),
                              MONO_BLACK_CONTROL: (-0.8, 0, -0.6), MONO_BLACK_AGGRO: (-0.6, 0.8, 0)})

def test_a_perfect_parallelogram_scores_perfectly() -> None:
    [score] = build_analogy_scores(PARALLELOGRAM, [CONTROL_RATHER_THAN_MIDRANGE])
    assert np.isclose(score.offset_cosine, 1.0)
    assert (score.rank_add, score.rank_mul, score.rank_only_b) == (1, 1, 2)  # Near Mono Black Midrange alone, Mono Black Aggro is nearer.

def test_the_offset_scores_of_the_parallelogram() -> None:
    add, _ = build_offset_scores(PARALLELOGRAM, CONTROL_RATHER_THAN_MIDRANGE)
    assert np.isclose(score_of(PARALLELOGRAM, add, MONO_BLACK_CONTROL), 1.0)
    assert np.isclose(score_of(PARALLELOGRAM, add, MONO_BLACK_AGGRO), 0.48)
    assert np.isclose(score_of(PARALLELOGRAM, add, MONO_BLACK_MIDRANGE), 0.28)  # It would score only 0.28, but the inputs are left out anyway.


# Scenario: 3CosMul resists one dominant term.

DOMINANT = centroids_at({ORZHOV_MIDRANGE: (1, 0, 0), ORZHOV_CONTROL: (0, 0, 1), MONO_BLACK_MIDRANGE: (0, 1, 0), MONO_BLACK_CONTROL: (-1, 0, 1),
                         MONO_BLACK_DEVOTION: (-1, 2, 1)})

def test_3cosmul_resists_one_dominant_term() -> None:
    add, mul = build_offset_scores(DOMINANT, CONTROL_RATHER_THAN_MIDRANGE)
    assert np.isclose(score_of(DOMINANT, add, MONO_BLACK_DEVOTION), 1.6330, atol=5e-5)
    assert np.isclose(score_of(DOMINANT, add, MONO_BLACK_CONTROL), 1.4142, atol=5e-5)
    assert np.isclose(score_of(DOMINANT, mul, MONO_BLACK_CONTROL), 2.8944, atol=5e-4)
    assert np.isclose(score_of(DOMINANT, mul, MONO_BLACK_DEVOTION), 2.1542, atol=5e-4)
    [score] = build_analogy_scores(DOMINANT, [CONTROL_RATHER_THAN_MIDRANGE])
    assert (score.rank_add, score.rank_mul, score.rank_only_b) == (2, 1, 2)
    assert np.isclose(score.offset_cosine, 0.7071, atol=5e-5)


# Scenario: the only-b baseline shows an analogy that needed no offset.

def test_the_only_b_baseline_shows_an_analogy_that_needed_no_offset() -> None:
    centroids = centroids_at({ORZHOV_MIDRANGE: (1, 0, 0), ORZHOV_CONTROL: (0, 0, 1), MONO_BLACK_MIDRANGE: (0, 1, 0), MONO_BLACK_CONTROL: (1, 5, 1),
                              MONO_BLACK_AGGRO: (1, 1, 0)})
    [score] = build_analogy_scores(centroids, [CONTROL_RATHER_THAN_MIDRANGE])
    assert (score.rank_add, score.rank_mul, score.rank_only_b) == (1, 1, 1)
    assert np.isclose(score.offset_cosine, 0.0, atol=1e-12)
    index = centroids.index()
    assert np.isclose(centroids.unit[index[MONO_BLACK_CONTROL]] @ centroids.unit[index[MONO_BLACK_MIDRANGE]], 0.9623, atol=5e-5)
