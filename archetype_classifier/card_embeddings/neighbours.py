"""A card's nearest neighbours in a set of card embeddings, by cosine similarity."""
from collections.abc import Collection
from dataclasses import dataclass

from archetype_classifier.card_embeddings.embeddings import Embeddings


@dataclass(frozen=True)
class Neighbour:
    name: str
    similarity: float


def build_neighbours(embeddings: Embeddings, card: str, n: int, among: Collection[str] | None = None) -> list[Neighbour]:
    """The n cards most similar to the card, best first, ties broken by name; the card itself is left out. among limits the cards searched."""
    if card not in embeddings.names:
        raise ValueError(f'{card} is not in these embeddings')
    similarities = embeddings.matrix @ embeddings.matrix[embeddings.names.index(card)]  # Rows are unit length, so a dot product is the cosine.
    candidates = [(float(s), name) for name, s in zip(embeddings.names, similarities) if name != card and (among is None or name in among)]
    return [Neighbour(name, s) for s, name in sorted(candidates, key=lambda c: (-c[0], c[1]))[:n]]
