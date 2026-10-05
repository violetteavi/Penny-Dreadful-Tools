"""Card embeddings: one unit-length row per card, in name order, with a manifest saying how they were made."""
from collections.abc import Sequence
from dataclasses import asdict, dataclass

import numpy as np

from archetype_classifier.card_embeddings.encoders import Encoder
from archetype_classifier.card_embeddings.pool import Card
from archetype_classifier.card_embeddings.text import TEXT_VERSION, TextRecipe, build_card_text
from archetype_classifier.evaluation.model import JSON

TOLERANCE = 1e-5  # How far a card's vector may move between runs (batching noise) and still count as the same.


@dataclass(frozen=True)
class Embeddings:
    names: tuple[str, ...]
    matrix: np.ndarray  # One unit-length row per name.
    manifest: dict[str, JSON]


def build_embeddings(cards: Sequence[Card], recipe: TextRecipe, encoder: Encoder) -> Embeddings:
    ordered = sorted(cards, key=lambda c: c.name)
    texts = [build_card_text(c, recipe) for c in ordered]
    matrix = encoder.encode(texts).astype(np.float32)
    matrix /= np.linalg.norm(matrix, axis=1, keepdims=True)
    manifest: dict[str, JSON] = {'encoder': encoder.name, 'revision': encoder.revision, 'recipe': asdict(recipe), 'text_version': TEXT_VERSION,
                                 'cards': len(ordered), 'max_tokens': encoder.max_tokens,
                                 'over_token_limit': sum(n > encoder.max_tokens for n in encoder.token_counts(texts))}
    return Embeddings(tuple(c.name for c in ordered), matrix, manifest)
