"""Analogies (#64; Scenarios.md, "Archetype geometry"): a : a* :: b : b*, asking whether a -> a* and b -> b* are the same direction.

On unit centroids, with a, a* and b left out of every search:
- 3CosAdd ranks each centroid d by cos(d, a*) - cos(d, a) + cos(d, b), the nearest to a* - a + b (Mikolov et al. 2013; Levy & Goldberg 2014).
- 3CosMul rescales each cosine to (cos + 1) / 2 and ranks by cos'(d, a*) cos'(d, b) / (cos'(d, a) + 0.001), so one large term can't carry a candidate
  that fails another (Levy & Goldberg 2014).
- Only-b ranks by cos(d, b) alone, the baseline an analogy has to beat (Linzen 2016).
- The offset cosine, cos(a* - a, b* - b), tests "same direction" with no search at all (Fournier et al. 2020). Its percentile is the share of
  random quadruples of distinct centroids, drawn with a fixed seed, whose offset cosine is lower.
A rank is 1 + the candidates scoring strictly higher than b*.
"""
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

import numpy as np

from archetype_classifier.geometry.centroids import Centroids

STRATEGIES = ('Control', 'Midrange', 'Aggro')
EPSILON = 0.001  # 3CosMul's guard against dividing by 0 (Levy & Goldberg 2014).
QUADRUPLES = 1000  # Random quadruples in the offset cosine's baseline.
type Kind = Literal['strategy', 'pair']


@dataclass(frozen=True)
class Analogy:
    a: int
    a_star: int
    b: int
    b_star: int
    kind: Kind

@dataclass(frozen=True)
class AnalogyScore:
    analogy: Analogy
    rank_add: int
    rank_mul: int
    rank_only_b: int
    offset_cosine: float
    offset_percentile: float | None  # None with no baseline (fewer than 4 centroids).


def build_strategy_analogies(names: Mapping[int, str], centroids: Centroids, strategies: Sequence[str] = STRATEGIES) -> list[Analogy]:
    """From names "X S" with S a strategy: X S : X T :: Y S : Y T for every two colours X != Y and strategies S != T where all four have centroids.
    A name that doesn't end in a strategy is never used."""
    split = {}
    for label in centroids.label_ids.tolist():
        for strategy in strategies:
            if names[label].endswith(f' {strategy}'):
                split[(names[label].removesuffix(f' {strategy}'), strategy)] = label
    colours = sorted({colour for colour, _ in split})
    return [Analogy(split[(x, s)], split[(x, t)], split[(y, s)], split[(y, t)], 'strategy')
            for x in colours for y in colours if x != y for s in strategies for t in strategies
            if s != t and all(key in split for key in ((x, s), (x, t), (y, s), (y, t)))]


def build_pair_analogies(pairs: Sequence[tuple[str, str]], names: Mapping[int, str], centroids: Centroids) -> tuple[list[Analogy], list[str]]:
    """From (fair, combo) pairs, for every two pairs: adding the combo (fair1 : combo1 :: fair2 : combo2) and taking it away (combo1 : fair1 ::
    combo2 : fair2). A pair with an archetype that has no centroid is skipped, and named in the second list."""
    ids = {names[label]: label for label in centroids.label_ids.tolist()}
    kept = [(ids[fair], ids[combo]) for fair, combo in pairs if fair in ids and combo in ids]
    skipped = [f'{fair} -> {combo}' for fair, combo in pairs if fair not in ids or combo not in ids]
    analogies = [Analogy(f1, c1, f2, c2, 'pair') for f1, c1 in kept for f2, c2 in kept if f1 != f2]
    return [*analogies, *(Analogy(c1, f1, c2, f2, 'pair') for f1, c1, f2, c2 in ((a.a, a.a_star, a.b, a.b_star) for a in analogies))], skipped


def build_offset_scores(centroids: Centroids, analogy: Analogy) -> tuple[np.ndarray, np.ndarray]:
    """Every centroid's 3CosAdd and 3CosMul scores, in centroid order, the inputs included (they're left out when ranking)."""
    index = centroids.index()
    cos_a_star, cos_a, cos_b = (centroids.unit @ centroids.unit[index[label]] for label in (analogy.a_star, analogy.a, analogy.b))
    add = cos_a_star - cos_a + cos_b
    mul = ((cos_a_star + 1) / 2) * ((cos_b + 1) / 2) / ((cos_a + 1) / 2 + EPSILON)
    return add, mul


def build_offset_baseline(centroids: Centroids, quadruples: int = QUADRUPLES, seed: int = 0) -> np.ndarray:
    """The offset cosines of random quadruples of distinct centroids: what "same direction" looks like by chance."""
    if len(centroids.label_ids) < 4:
        return np.zeros(0)
    rng = np.random.default_rng(seed)
    picks = np.array([rng.choice(len(centroids.label_ids), size=4, replace=False) for _ in range(quadruples)])
    return np.array([offset_cosine(centroids.unit, *quadruple) for quadruple in picks.tolist()])


def offset_cosine(unit: np.ndarray, a: int, a_star: int, b: int, b_star: int) -> float:
    offset_a, offset_b = unit[a_star] - unit[a], unit[b_star] - unit[b]
    return float(offset_a @ offset_b / (np.linalg.norm(offset_a) * np.linalg.norm(offset_b)))


def build_analogy_scores(centroids: Centroids, analogies: Sequence[Analogy], quadruples: int = QUADRUPLES, seed: int = 0) -> list[AnalogyScore]:
    index = centroids.index()
    baseline = build_offset_baseline(centroids, quadruples, seed)
    scores = []
    for analogy in analogies:
        add, mul = build_offset_scores(centroids, analogy)
        only_b = centroids.unit @ centroids.unit[index[analogy.b]]
        candidates = np.ones(len(centroids.label_ids), dtype=bool)
        candidates[[index[analogy.a], index[analogy.a_star], index[analogy.b]]] = False
        target = index[analogy.b_star]
        rank_add, rank_mul, rank_only_b = (1 + int((s[candidates] > s[target]).sum()) for s in (add, mul, only_b))
        cosine = offset_cosine(centroids.unit, index[analogy.a], index[analogy.a_star], index[analogy.b], target)
        percentile = float((baseline < cosine).mean()) if len(baseline) else None
        scores.append(AnalogyScore(analogy, rank_add, rank_mul, rank_only_b, cosine, percentile))
    return scores
