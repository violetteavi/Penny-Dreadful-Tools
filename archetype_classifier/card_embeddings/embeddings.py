"""Card embeddings: one unit-length row per card, in name order, with a manifest saying how they were made.

They are saved as <encoder>__<recipe>.npy beside a .json holding the manifest and the card names, in archetype_classifier/embeddings/ (gitignored).
"""
import json
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, cast

import numpy as np

from archetype_classifier.card_embeddings.encoders import Encoder
from archetype_classifier.card_embeddings.pool import Card
from archetype_classifier.card_embeddings.text import TEXT_VERSION, TextRecipe, build_card_text
from archetype_classifier.evaluation.model import JSON

EMBEDDINGS_DIR = Path(__file__).parents[1] / 'embeddings'
TOLERANCE = 1e-5  # How far a card's vector may move between runs (batching noise) and still count as the same.


@dataclass(frozen=True)
class Embeddings:
    names: tuple[str, ...]
    matrix: np.ndarray  # One unit-length row per name.
    manifest: dict[str, JSON]

    def similarities(self, start: int, stop: int) -> np.ndarray:
        """The cosine similarity of cards start to stop with every card: rows are unit length, so it's a dot product."""
        return self.matrix[start:stop] @ self.matrix.T


def build_embeddings(cards: Sequence[Card], recipe: TextRecipe, encoder: Encoder) -> Embeddings:
    ordered = sorted(cards, key=lambda c: c.name)
    texts = [build_card_text(c, recipe) for c in ordered]
    matrix = encoder.encode(texts).astype(np.float32)
    matrix /= np.linalg.norm(matrix, axis=1, keepdims=True)
    manifest: dict[str, JSON] = {'encoder': encoder.name, 'revision': encoder.revision, 'recipe': asdict(recipe), 'text_version': TEXT_VERSION,
                                 'cards': len(ordered), 'max_tokens': encoder.max_tokens,
                                 'over_token_limit': 0 if encoder.max_tokens is None else sum(n > encoder.max_tokens for n in encoder.token_counts(texts))}
    return Embeddings(tuple(c.name for c in ordered), matrix, manifest)

IDENTITY = ('encoder', 'revision', 'recipe', 'text_version', 'max_tokens')  # Manifest fields that must match for embeddings to be merged.


def merge_embeddings(a: Embeddings, b: Embeddings) -> Embeddings:
    """Both sets of rows in one, in name order: how a new set's cards are added without re-embedding the old ones."""
    if any(a.manifest[k] != b.manifest[k] for k in IDENTITY):
        raise ValueError('Only embeddings from the same encoder, revision, recipe and text version can be merged')
    if repeated := sorted(set(a.names) & set(b.names)):
        raise ValueError(f'Already embedded: {", ".join(repeated)}')
    names = a.names + b.names
    order = sorted(range(len(names)), key=lambda i: names[i])
    manifest = {**a.manifest, 'cards': len(names), 'over_token_limit': cast(int, a.manifest['over_token_limit']) + cast(int, b.manifest['over_token_limit'])}
    return Embeddings(tuple(names[i] for i in order), np.concatenate([a.matrix, b.matrix])[order], manifest)

def embeddings_path(directory: Path, encoder: str, recipe: TextRecipe) -> Path:
    return directory / f'{encoder}__{recipe.label}.npy'

def save_embeddings(embeddings: Embeddings, directory: Path = EMBEDDINGS_DIR) -> Path:
    """Writes the .npy and its .json, and returns the .npy's path."""
    path = embeddings_path(directory, str(embeddings.manifest['encoder']), TextRecipe(**cast(dict[str, Any], embeddings.manifest['recipe'])))
    directory.mkdir(parents=True, exist_ok=True)
    np.save(path, embeddings.matrix)
    path.with_suffix('.json').write_text(json.dumps({'manifest': embeddings.manifest, 'names': embeddings.names}, indent=1))
    return path

def load_embeddings(path: Path) -> Embeddings:
    matrix = np.load(path)
    saved = json.loads(path.with_suffix('.json').read_text())
    if len(saved['names']) != matrix.shape[0]:
        raise ValueError(f"{path.name} has {matrix.shape[0]} rows but its manifest lists {len(saved['names'])} cards")
    return Embeddings(tuple(saved['names']), matrix, saved['manifest'])
