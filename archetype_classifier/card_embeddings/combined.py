"""Text embeddings combined with structured vectors, so similarity weighs what a card does against its numbers.

Structured columns are standardised with statistics fitted once and then frozen, so standardising a new set's cards never moves an existing card's row.
The combined vector for a card is [sqrt(alpha) * text, sqrt(1 - alpha) * structured / |structured|], so the dot product of two combined vectors is
alpha * text cosine + (1 - alpha) * structured cosine, and the result is an ordinary Embeddings that the neighbour functions work on unchanged.
"""
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

import numpy as np

from archetype_classifier.card_embeddings.embeddings import Embeddings
from archetype_classifier.card_embeddings.structured import FrontNumbers


@dataclass(frozen=True)
class Standardisation:
    mean: np.ndarray
    scale: np.ndarray  # The column's standard deviation, or 1 for a column that never varies.

    def apply(self, rows: np.ndarray) -> np.ndarray:
        return ((rows - self.mean) / self.scale).astype(np.float32)


def build_standardisation(matrix: np.ndarray) -> Standardisation:
    std = matrix.std(axis=0)
    return Standardisation(matrix.mean(axis=0), np.where(std > 0, std, 1.0))

def build_combined(text: Embeddings, structured: np.ndarray, alpha: float, scheme: str | None = None) -> Embeddings:
    """Rows of structured must follow text.names. A card whose structured row is all zeros keeps only its text part."""
    if structured.shape[0] != len(text.names):
        raise ValueError(f'{len(text.names)} cards of text but {structured.shape[0]} structured rows')
    norms = np.linalg.norm(structured, axis=1, keepdims=True)
    unit = np.divide(structured, norms, out=np.zeros_like(structured, dtype=np.float32), where=norms > 0)
    matrix = np.hstack([np.sqrt(alpha) * text.matrix, np.sqrt(1 - alpha) * unit]).astype(np.float32)
    manifest = {**text.manifest, 'alpha': alpha, **({'structured': scheme} if scheme else {})}
    return Embeddings(text.names, matrix, manifest)

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
    text: Embeddings
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
