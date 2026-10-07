"""The combined embedding: each card's masked-text embedding together with its card numbers, combined by an approach with weights, and stored so
that later work loads it rather than rebuilding it. The maths of each approach lives in combined.py.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class CombinedEmbeddingWeights:
    """How much the text, mana value, colour and stats count. Only the ratios matter: they're stored divided by the sum of all four."""
    text: float
    mana_value: float
    colour: float
    stats: float

    def __post_init__(self) -> None:
        total = self.text + self.mana_value + self.colour + self.stats
        for name in ('text', 'mana_value', 'colour', 'stats'):
            object.__setattr__(self, name, getattr(self, name) / total)
