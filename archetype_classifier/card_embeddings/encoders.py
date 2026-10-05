"""Frozen text encoders that turn card text into vectors.

Each is a sentence-transformers model pinned to a Hugging Face revision. They need the optional archetypes dependency group (uv sync --group archetypes),
imported only when an encoder is loaded, so the rest of the package works without torch.
"""
import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Protocol

import numpy as np

BATCH_SIZE = 64


class Encoder(Protocol):
    name: str
    revision: str  # The pinned model revision, so embeddings can be rebuilt exactly.
    max_tokens: int | None  # Text past this many tokens is cut off; None for no limit.

    def encode(self, texts: Sequence[str]) -> np.ndarray: ...

    def token_counts(self, texts: Sequence[str]) -> list[int]: ...

@dataclass(frozen=True)
class EncoderSpec:
    model_id: str
    revision: str
    dimensions: int

ENCODERS = {
    'bge-small': EncoderSpec('BAAI/bge-small-en-v1.5', '5c38ec7c405ec4b44b94cc5a9bb96e735b38267a', 384),
    'bge-base': EncoderSpec('BAAI/bge-base-en-v1.5', 'a5beb1e3e68b9ab74eb54cfd186867f64f240e1a', 768),
    'potion': EncoderSpec('minishlab/potion-base-8M', 'bf8b056651a2c21b8d2565580b8569da283cab23', 256),
    'minilm': EncoderSpec('sentence-transformers/all-MiniLM-L6-v2', '1110a243fdf4706b3f48f1d95db1a4f5529b4d41', 384),
    'gte-modernbert': EncoderSpec('Alibaba-NLP/gte-modernbert-base', 'e7f32e3c00f91d699e8c43b53106206bcc72bb22', 768),
}


class SentenceTransformerEncoder:
    def __init__(self, name: str, spec: EncoderSpec, model: Any) -> None:
        self.name = name
        self.revision = spec.revision
        self.model = model
        self.max_tokens = None if model.max_seq_length == math.inf else int(model.max_seq_length)  # A static model has no limit.

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        return np.asarray(self.model.encode(list(texts), batch_size=BATCH_SIZE, convert_to_numpy=True, show_progress_bar=False))

    def token_counts(self, texts: Sequence[str]) -> list[int]:
        """How many tokens each text has before any cut-off."""
        tokenizer = self.model.tokenizer
        if hasattr(tokenizer, 'encode_batch'):  # A static model's tokenizers.Tokenizer.
            return [len(e.ids) for e in tokenizer.encode_batch(list(texts))]
        return [len(ids) for ids in tokenizer(list(texts), truncation=False)['input_ids']]


def load_encoder(name: str) -> Encoder:
    if name not in ENCODERS:
        raise ValueError(f'No encoder called {name}; known: {", ".join(sorted(ENCODERS))}')
    from sentence_transformers import SentenceTransformer  # noqa: PLC0415  # Optional dependency, imported only when needed.
    spec = ENCODERS[name]
    return SentenceTransformerEncoder(name, spec, SentenceTransformer(spec.model_id, revision=spec.revision, device='cpu'))
