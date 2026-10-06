"""Text embeddings combined with structured vectors, so similarity weighs what a card does against its numbers.

Structured columns are standardised with statistics fitted once and then frozen, so standardising a new set's cards never moves an existing card's row.
The combined vector for a card is [sqrt(alpha) * text, sqrt(1 - alpha) * structured / |structured|], so the dot product of two combined vectors is
alpha * text cosine + (1 - alpha) * structured cosine, and the result is an ordinary Embeddings that the neighbour functions work on unchanged.
"""
from dataclasses import dataclass

import numpy as np

from archetype_classifier.card_embeddings.embeddings import Embeddings


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
