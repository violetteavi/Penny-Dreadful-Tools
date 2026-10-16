"""Analogies (Scenarios.md, "Archetype geometry")."""
from collections.abc import Mapping, Sequence

import numpy as np

from archetype_classifier.geometry.analogies import Analogy, build_analogy_scores, build_offset_baseline, build_offset_scores, build_pair_analogies, build_strategy_analogies
from archetype_classifier.geometry.centroids import Centroids, build_centroids
from archetype_classifier.geometry.space_test import rows_space

ORZHOV_MIDRANGE, ORZHOV_CONTROL, MONO_BLACK_MIDRANGE, MONO_BLACK_CONTROL, MONO_BLACK_AGGRO, MONO_BLACK_DEVOTION = 356, 512, 282, 18, 13, 324
CONTROL_RATHER_THAN_MIDRANGE = Analogy(ORZHOV_MIDRANGE, ORZHOV_CONTROL, MONO_BLACK_MIDRANGE, MONO_BLACK_CONTROL, 'strategy')

def centroids_at(points: Mapping[int, Sequence[float]]) -> Centroids:
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


# The offset cosine's baseline: offset cosines of random quadruples of distinct centroids, repeatable for a seed.

def test_the_random_baseline_is_repeatable_for_a_seed() -> None:
    first, again, other = (build_offset_baseline(DOMINANT, quadruples=200, seed=s) for s in (0, 0, 1))
    assert np.array_equal(first, again)
    assert not np.array_equal(first, other)
    assert len(first) == 200 and np.all(np.abs(first) <= 1 + 1e-12)

def test_the_offset_percentile_is_the_share_of_random_quadruples_below() -> None:
    [score] = build_analogy_scores(DOMINANT, [CONTROL_RATHER_THAN_MIDRANGE], quadruples=200, seed=0)
    baseline = build_offset_baseline(DOMINANT, quadruples=200, seed=0)
    assert score.offset_percentile is not None
    assert np.isclose(score.offset_percentile, float((baseline < score.offset_cosine).mean()))
    assert 0 < score.offset_percentile < 1

def test_too_few_centroids_for_a_quadruple_give_no_baseline() -> None:
    three = centroids_at({ORZHOV_MIDRANGE: (1, 0, 0), ORZHOV_CONTROL: (0, 0, 1), MONO_BLACK_MIDRANGE: (0, 1, 0)})
    assert len(build_offset_baseline(three, quadruples=200, seed=0)) == 0


# Scenario: analogies test if strategies have a consistent direction. Which analogies are built from which archetypes.

ORZHOV_ARISTOCRATS, APPLEJACKS, LUMBERTWIN, IZZET_CONTROL, IZZET_TWIN = 60, 561, 633, 65, 549
NAMES = {ORZHOV_MIDRANGE: 'Orzhov Midrange', ORZHOV_CONTROL: 'Orzhov Control', MONO_BLACK_MIDRANGE: 'Mono Black Midrange', MONO_BLACK_CONTROL: 'Mono Black Control',
         MONO_BLACK_AGGRO: 'Mono Black Aggro', MONO_BLACK_DEVOTION: 'Mono Black Devotion', ORZHOV_ARISTOCRATS: 'Orzhov Aristocrats',
         APPLEJACKS: 'Applejacks', LUMBERTWIN: 'Lumbertwin', IZZET_CONTROL: 'Izzet Control', IZZET_TWIN: 'Izzet Twin'}
EVERY_ONE = centroids_at({label: tuple(float(i == j) for j in range(len(NAMES))) for i, label in enumerate(NAMES)})  # Every archetype has a centroid.

def test_strategy_analogies_pair_two_colours_with_two_strategies() -> None:
    analogies = build_strategy_analogies(NAMES, EVERY_ONE)
    assert set(analogies) == {Analogy(ORZHOV_MIDRANGE, ORZHOV_CONTROL, MONO_BLACK_MIDRANGE, MONO_BLACK_CONTROL, 'strategy'),
                              Analogy(ORZHOV_CONTROL, ORZHOV_MIDRANGE, MONO_BLACK_CONTROL, MONO_BLACK_MIDRANGE, 'strategy'),
                              Analogy(MONO_BLACK_MIDRANGE, MONO_BLACK_CONTROL, ORZHOV_MIDRANGE, ORZHOV_CONTROL, 'strategy'),
                              Analogy(MONO_BLACK_CONTROL, MONO_BLACK_MIDRANGE, ORZHOV_CONTROL, ORZHOV_MIDRANGE, 'strategy')}
    assert len(analogies) == 4

def test_pair_analogies_add_the_combo_and_take_it_away_each_way() -> None:
    analogies, skipped = build_pair_analogies([('Applejacks', 'Lumbertwin'), ('Izzet Control', 'Izzet Twin')], NAMES, EVERY_ONE)
    assert set(analogies) == {Analogy(APPLEJACKS, LUMBERTWIN, IZZET_CONTROL, IZZET_TWIN, 'pair'), Analogy(IZZET_CONTROL, IZZET_TWIN, APPLEJACKS, LUMBERTWIN, 'pair'),
                              Analogy(LUMBERTWIN, APPLEJACKS, IZZET_TWIN, IZZET_CONTROL, 'pair'), Analogy(IZZET_TWIN, IZZET_CONTROL, LUMBERTWIN, APPLEJACKS, 'pair')}
    assert len(analogies) == 4 and skipped == []

def test_without_a_centroid_an_archetype_is_never_in_an_analogy() -> None:
    without = centroids_at({label: v for label, v in zip(NAMES, np.eye(len(NAMES)).tolist(), strict=True) if label not in (MONO_BLACK_CONTROL, LUMBERTWIN)})
    assert build_strategy_analogies(NAMES, without) == []
    analogies, skipped = build_pair_analogies([('Applejacks', 'Lumbertwin'), ('Izzet Control', 'Izzet Twin'), ('Orzhov Midrange', 'Orzhov Aristocrats')], NAMES, without)
    assert skipped == ['Applejacks -> Lumbertwin']
    assert len(analogies) == 4  # The two pairs left, each way, adding and taking away.
