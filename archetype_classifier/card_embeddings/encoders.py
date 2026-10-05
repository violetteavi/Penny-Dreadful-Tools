"""Frozen text encoders that turn card text into vectors."""
from collections.abc import Sequence
from typing import Protocol

import numpy as np


class Encoder(Protocol):
    name: str
    revision: str  # The pinned model revision, so embeddings can be rebuilt exactly.
    max_tokens: int  # Text past this many tokens is cut off.

    def encode(self, texts: Sequence[str]) -> np.ndarray: ...

    def token_counts(self, texts: Sequence[str]) -> list[int]: ...
