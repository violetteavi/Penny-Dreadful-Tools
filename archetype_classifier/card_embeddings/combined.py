"""A card's text embedding combined with its numbers (structured.py), so similarity weighs what a card does against its cost, colours and stats.

Two approaches, both weighting mana value, colour and stats a third each and mixing in the text cosine by alpha:
- exact thirds (GroupedSimilarity): each group compared on its own terms, combined as a similarity rather than a vector;
- average thirds (AverageThirds with build_combined): one vector per card, scaled so each group makes up a third on average, compared by a cosine.

Every statistic (centring means, standardisation, fill values, group scales) is fitted once and frozen, so a new set's cards never move an existing card.
build_combined joins [sqrt(alpha) * text, sqrt(1 - alpha) * structured / |structured|], so the dot product of two combined vectors is
alpha * text cosine + (1 - alpha) * structured cosine, and the result is an ordinary TextEmbeddings that the neighbour functions work on unchanged.
"""
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

import numpy as np

from archetype_classifier.card_embeddings.structured import SCALARS, WUBRG, FrontNumbers
from archetype_classifier.card_embeddings.text_embedding import TextEmbeddings


@dataclass(frozen=True)
class Standardisation:
    mean: np.ndarray
    scale: np.ndarray  # Each column's divisor: 1 when the column is only centred.

    def apply(self, rows: np.ndarray) -> np.ndarray:
        return ((rows - self.mean) / self.scale).astype(np.float32)


def build_combined(text: TextEmbeddings, structured: np.ndarray, alpha: float, scheme: str | None = None) -> TextEmbeddings:
    """Rows of structured must follow text.names. A card whose structured row is all zeros keeps only its text part."""
    if structured.shape[0] != len(text.names):
        raise ValueError(f'{len(text.names)} cards of text but {structured.shape[0]} structured rows')
    norms = np.linalg.norm(structured, axis=1, keepdims=True)
    unit = np.divide(structured, norms, out=np.zeros_like(structured, dtype=np.float32), where=norms > 0)
    matrix = np.hstack([np.sqrt(alpha) * text.matrix, np.sqrt(1 - alpha) * unit]).astype(np.float32)
    manifest = {**text.manifest, 'alpha': alpha, **({'structured': scheme} if scheme else {})}
    return TextEmbeddings(text.names, matrix, manifest)

def build_group_shares(rows: np.ndarray, columns: Sequence[str], group_of: Callable[[str], str]) -> dict[str, float]:
    """Each column group's share of a row's squared length, averaged over the rows that aren't all zero: how much each group can move a cosine."""
    squares = rows.astype(np.float64) ** 2
    totals = squares.sum(axis=1)
    kept = squares[totals > 0] / totals[totals > 0, None]
    groups = [group_of(c) for c in columns]
    return {g: float(kept[:, [i for i, x in enumerate(groups) if x == g]].sum(axis=1).mean()) for g in dict.fromkeys(groups)}


def build_centring(matrix: np.ndarray) -> Standardisation:
    """Subtract each column's mean, fitted once and frozen, without dividing by its spread: for yes/no columns, so rare values aren't inflated."""
    return Standardisation(matrix.mean(axis=0), np.ones(matrix.shape[1]))


# Stage 2d: exact thirds (#7 spec, 2026-10-05).
# similarity = alpha * text cosine + (1 - alpha) * (w_mv * mana value + w_colour * colour + w_stats * stats), where
# - mana value: 0 if the (present, variable) pairs differ, otherwise exp(-|v_a - v_b|) on log values;
# - stats: 0 if any of power, toughness and loyalty has differing pairs, otherwise exp(-sum |v_a - v_b|);
# - colour: (cosine of the centred W U B R G columns + 1) / 2.
# Every group runs from 0 to 1, so the weights start even.

THIRDS = (1 / 3, 1 / 3, 1 / 3)


@dataclass(frozen=True)
class GroupedSimilarity:
    text: TextEmbeddings
    numbers: FrontNumbers
    centring: Standardisation
    alpha: float
    weights: tuple[float, float, float] = THIRDS  # Mana value, colour, stats.
    log_values: np.ndarray = field(init=False, repr=False)
    colours: np.ndarray = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if self.text.names != self.numbers.names:
            raise ValueError('The text and the numbers are for different cards, or in a different order')
        centred = self.centring.apply(self.numbers.colours).astype(np.float64)
        object.__setattr__(self, 'log_values', self.numbers.log_values())
        object.__setattr__(self, 'colours', centred / np.linalg.norm(centred, axis=1, keepdims=True))

    @property
    def names(self) -> tuple[str, ...]:
        return self.text.names

    def similarities(self, start: int, stop: int) -> np.ndarray:
        mana_value, colour, stats = self.group_blocks(start, stop)
        w_mv, w_colour, w_stats = self.weights
        structured = w_mv * mana_value + w_colour * colour + w_stats * stats
        return (self.alpha * self.text.similarities(start, stop) + (1 - self.alpha) * structured).astype(np.float32)

    def group_blocks(self, start: int, stop: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Mana value, colour and stats similarities of cards start to stop with every card."""
        rows = slice(start, stop)
        mana_value_matches, mana_value_difference = self.scalar_block(rows, 0)
        mana_value = np.where(mana_value_matches, np.exp(-mana_value_difference), 0.0)
        stats_matches, stats_difference = self.scalar_block(rows, 1)
        for column in (2, 3):  # Toughness and loyalty, one at a time to keep memory to one block per array.
            matches, difference = self.scalar_block(rows, column)
            stats_matches &= matches
            stats_difference += difference
        stats = np.where(stats_matches, np.exp(-stats_difference), 0.0)
        colour = (self.colours[rows] @ self.colours.T + 1) / 2
        return mana_value, colour, stats

    def scalar_block(self, rows: slice, column: int) -> tuple[np.ndarray, np.ndarray]:
        """Whether each pair's (present, variable) flags match for one scalar, and the absolute difference of their log values."""
        n = self.numbers
        matches = (n.present[rows, column, None] == n.present[None, :, column]) & (n.variable[rows, column, None] == n.variable[None, :, column])
        return matches, np.abs(self.log_values[rows, column, None] - self.log_values[None, :, column])

    def group_similarities(self, a: str, b: str) -> dict[str, float]:
        """Each group's score for one pair, with the text cosine, the structured similarity and the combined similarity: for the diagnostics."""
        i, j = self.names.index(a), self.names.index(b)
        mana_value, colour, stats = (float(block[0, j]) for block in self.group_blocks(i, i + 1))
        w_mv, w_colour, w_stats = self.weights
        structured = w_mv * mana_value + w_colour * colour + w_stats * stats
        text = float(self.text.similarities(i, i + 1)[0, j])
        return {'text': text, 'mana value': mana_value, 'colour': colour, 'stats': stats, 'structured': structured,
                'similarity': self.alpha * text + (1 - self.alpha) * structured}


# The comparison approach, average thirds (#7 spec, 2026-10-05): one vector per card, compared by a single cosine. Yes/no columns (each scalar's present
# and variable flags, the colours) are centred; each scalar's value is logged and standardised, with a missing value filled by the mean (0 after
# standardising) and a variable one set to its fixed part plus the mean of the fixed values. One scale per group, fitted so that mana value, colour and
# stats each make up a third of a card's squared length on average. Every statistic is fitted once and frozen.

def scalar_columns(scalar: str) -> tuple[str, ...]:
    return f'{scalar}.present', f'{scalar}.variable', f'{scalar}.value'

AVERAGE_THIRDS_COLUMNS = (*scalar_columns('mana_value'), *(f'colour.{c}' for c in WUBRG), *(c for s in SCALARS[1:] for c in scalar_columns(s)))
GROUPS = ('mana value', 'colour', 'stats')
SCALE_FITTING_ROUNDS = 200


def average_thirds_group(column: str) -> str:
    return {'mana_value': 'mana value', 'colour': 'colour'}.get(column.split('.')[0], 'stats')


@dataclass(frozen=True)
class AverageThirds:
    flag_means: np.ndarray  # Rows present, variable; one column per scalar.
    colour_means: np.ndarray
    value_means: np.ndarray  # Each scalar's mean over present, fixed values, in raw units.
    log_means: np.ndarray
    log_stds: np.ndarray
    scales: np.ndarray  # One per group, in GROUPS order.

    def raw_values(self, numbers: FrontNumbers) -> np.ndarray:
        """Fixed values as written; a variable value is its fixed part plus (or, for 7-*, minus) the mean; a missing value is the mean."""
        filled = np.where(numbers.variable, numbers.fixed + numbers.sign * self.value_means, numbers.fixed)
        return np.where(numbers.present, filled, self.value_means)

    def standardised(self, numbers: FrontNumbers) -> np.ndarray:
        """The columns before group scaling, in AVERAGE_THIRDS_COLUMNS order."""
        values = (np.log(np.maximum(1.0, 1.0 + self.raw_values(numbers))) - self.log_means) / self.log_stds
        values = np.where(numbers.present, values, 0.0)
        present = numbers.present - self.flag_means[0]
        variable = numbers.variable - self.flag_means[1]
        blocks = [np.stack([present[:, i], variable[:, i], values[:, i]], axis=1) for i in range(len(SCALARS))]
        return np.hstack([blocks[0], numbers.colours - self.colour_means, *blocks[1:]])

    def apply(self, numbers: FrontNumbers) -> np.ndarray:
        column_scales = np.array([self.scales[GROUPS.index(average_thirds_group(c))] for c in AVERAGE_THIRDS_COLUMNS])
        return (self.standardised(numbers) * column_scales).astype(np.float32)


def build_average_thirds(numbers: FrontNumbers, shares: tuple[float, float, float]) -> AverageThirds:
    """Fits the statistics on these cards; shares is each group's target share of a card's squared length (THIRDS for average thirds)."""
    fixed = numbers.present & ~numbers.variable
    value_means = np.array([numbers.fixed[fixed[:, i], i].mean() if fixed[:, i].any() else 0.0 for i in range(len(SCALARS))])
    logs = np.log(np.maximum(1.0, 1.0 + numbers.fixed))
    log_means = np.array([logs[fixed[:, i], i].mean() if fixed[:, i].any() else 0.0 for i in range(len(SCALARS))])
    log_stds = np.array([logs[fixed[:, i], i].std() if fixed[:, i].any() else 0.0 for i in range(len(SCALARS))])
    fit = AverageThirds(np.stack([numbers.present.mean(axis=0), numbers.variable.mean(axis=0)]), numbers.colours.mean(axis=0), value_means,
                        log_means, np.where(log_stds > 0, log_stds, 1.0), np.ones(len(GROUPS)))
    return AverageThirds(fit.flag_means, fit.colour_means, fit.value_means, fit.log_means, fit.log_stds, build_group_scales(fit.standardised(numbers), shares))

def build_group_scales(rows: np.ndarray, shares: tuple[float, float, float]) -> np.ndarray:
    """One scale per group so that each group's share of a row's squared length averages its target share (in GROUPS order), found by repeatedly
    correcting each scale. A group with share 0 is scaled to 0 and left out, so the others share the rest; that is also the limit as its share
    shrinks, where fitting it would divide 0 by 0. Rows with no length are skipped; with none left, the kept groups keep scale 1."""
    squares = np.stack([(rows[:, [i for i, c in enumerate(AVERAGE_THIRDS_COLUMNS) if average_thirds_group(c) == g]] ** 2).sum(axis=1) for g in GROUPS], axis=1)
    targets = np.array(shares, dtype=np.float64)
    kept = targets > 0
    scales = np.where(kept, 1.0, 0.0)
    if not kept.any():
        return scales
    targets = targets[kept] / targets[kept].sum()
    squares = squares[:, kept][squares[:, kept].sum(axis=1) > 0]  # A row with no length in these groups has no shares; skip it, as build_group_shares does.
    for _ in range(SCALE_FITTING_ROUNDS if len(squares) else 0):
        weighted = squares * scales[kept] ** 2
        achieved = (weighted / weighted.sum(axis=1, keepdims=True)).mean(axis=0)
        scales[kept] *= np.sqrt(targets / achieved)
    return scales
