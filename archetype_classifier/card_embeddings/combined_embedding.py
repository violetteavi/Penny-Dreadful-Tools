"""The combined embedding: each card's masked-text embedding together with its card numbers, combined by an approach with weights, and stored so
that later work loads it rather than rebuilding it. The maths of each approach lives in combined.py.
"""
import math
import re
from collections.abc import Callable
from dataclasses import asdict, dataclass, fields
from typing import Any, ClassVar, Literal, Protocol

import numpy as np

from archetype_classifier.card_embeddings.combined import AverageThirds, build_average_thirds, build_combined
from archetype_classifier.card_embeddings.neighbours import Similarities
from archetype_classifier.card_embeddings.structured import FrontNumbers
from archetype_classifier.card_embeddings.text import TextRecipe
from archetype_classifier.card_embeddings.text_embedding import TextEmbeddings
from archetype_classifier.evaluation.model import JSON

CombiningApproach = Literal['average']  # 'exact' (exact thirds, combined.GroupedSimilarity) can join later.

WEIGHT_NAMES = ('text', 'mana_value', 'colour', 'stats')
SEASON_PART = re.compile(r'(\d+)(?:-(\d+))?')


@dataclass(frozen=True)
class CombinedEmbeddingWeights:
    """How much the text, mana value, colour and stats count. Only the ratios matter: they're stored divided by the sum of all four.

    Zeros are allowed: (1, 0, 0, 0) is the text alone and (2, 1, 1, 0) leaves stats out. Negative or non-finite weights, or all four 0, are refused.
    """
    text: float
    mana_value: float
    colour: float
    stats: float

    def __post_init__(self) -> None:
        given = {name: getattr(self, name) for name in WEIGHT_NAMES}
        if not all(math.isfinite(w) for w in given.values()):
            raise ValueError(f'Weights must be finite: {given}')
        if any(w < 0 for w in given.values()):
            raise ValueError(f'Weights must not be negative: {given}')
        total = sum(given.values())
        if total == 0:
            raise ValueError('The weights are all four 0: nothing would be compared')
        for name, w in given.items():
            object.__setattr__(self, name, w / total)



class TextAndNumbersCombiner(Protocol):
    """A fitted way of combining cards' text embeddings with their numbers: it carries its weights and its frozen statistics."""
    approach: ClassVar[CombiningApproach]

    @property
    def weights(self) -> CombinedEmbeddingWeights: ...

    def combine(self, text: TextEmbeddings, numbers: FrontNumbers) -> Similarities: ...

    def to_json(self) -> dict[str, JSON]:
        """The approach, the weights and the statistics: all that LOAD_COMBINER needs to rebuild it."""
        ...


@dataclass(frozen=True)
class AverageThirdsCombiner:
    """Average thirds: one vector per card, each number group scaled to its share of the numbers part on average, mixed with the text by its weight."""
    weights: CombinedEmbeddingWeights
    statistics: AverageThirds  # Fitted once, then frozen.
    approach: ClassVar[CombiningApproach] = 'average'

    def group_shares(self) -> tuple[float, float, float]:
        return build_group_shares(self.weights)

    def combine(self, text: TextEmbeddings, numbers: FrontNumbers) -> Similarities:
        return build_combined(text, self.statistics.apply(numbers), self.weights.text)

    def to_json(self) -> dict[str, JSON]:
        statistics: dict[str, JSON] = {f.name: getattr(self.statistics, f.name).tolist() for f in fields(AverageThirds)}
        return {'approach': self.approach, 'weights': asdict(self.weights), 'statistics': statistics}

def build_group_shares(weights: CombinedEmbeddingWeights) -> tuple[float, float, float]:
    """Each number group's weight over the three groups' total (mana value, colour, stats): the shares average thirds aims each group at.
    All 0 when the group weights are all 0, so the numbers drop out."""
    total = weights.mana_value + weights.colour + weights.stats
    return (weights.mana_value / total, weights.colour / total, weights.stats / total) if total else (0.0, 0.0, 0.0)

def build_average_thirds_combiner(numbers: FrontNumbers, weights: CombinedEmbeddingWeights) -> AverageThirdsCombiner:
    return AverageThirdsCombiner(weights, build_average_thirds(numbers, build_group_shares(weights)))

def build_average_thirds_combiner_from_json(saved: dict[str, Any]) -> AverageThirdsCombiner:
    statistics = AverageThirds(**{name: np.array(values) for name, values in saved['statistics'].items()})
    return AverageThirdsCombiner(CombinedEmbeddingWeights(**saved['weights']), statistics)

FIT_COMBINER: dict[CombiningApproach, Callable[[FrontNumbers, CombinedEmbeddingWeights], TextAndNumbersCombiner]] = {'average': build_average_thirds_combiner}
LOAD_COMBINER: dict[CombiningApproach, Callable[[dict[str, Any]], TextAndNumbersCombiner]] = {'average': build_average_thirds_combiner_from_json}

@dataclass(frozen=True)
class CombinedEmbeddingSettings:
    """Which text and which cards: every card legal in an embedded season is embedded, and the combiner's statistics are fitted on the cards
    legal in a fit season. Seasons are sets, so gaps are fine. No defaults: every caller says what it wants."""
    encoder: str  # A key of encoders.ENCODERS.
    recipe: TextRecipe
    fit_seasons: frozenset[int]
    embedded_seasons: frozenset[int]

    def __post_init__(self) -> None:
        if not self.fit_seasons:
            raise ValueError('There must be at least one fit season')
        if outside := self.fit_seasons - self.embedded_seasons:
            raise ValueError(f'The fit seasons {build_season_label(frozenset(outside))} are not embedded')


def build_season_set(text: str) -> frozenset[int]:
    """Seasons written as ranges and single seasons separated by commas: '1-3,6-8,10' is {1, 2, 3, 6, 7, 8, 10}."""
    seasons: set[int] = set()
    for part in text.split(','):
        match = SEASON_PART.fullmatch(part)
        first, last = (int(match[1]), int(match[2] or match[1])) if match else (0, 0)
        if not match or first < 1 or last < first:
            raise ValueError(f'Seasons must be written like 1-38 or 1-3,6,8, not {text!r}')
        seasons.update(range(first, last + 1))
    return frozenset(seasons)

def build_season_label(seasons: frozenset[int]) -> str:
    """The seasons as ranges for a file name: {1, 2, 3, 6, 7, 8, 10} is '1-3_6-8_10'."""
    runs: list[list[int]] = []
    for season in sorted(seasons):
        if runs and season == runs[-1][-1] + 1:
            runs[-1].append(season)
        else:
            runs.append([season])
    return '_'.join(str(r[0]) if len(r) == 1 else f'{r[0]}-{r[-1]}' for r in runs)
