"""The text an encoder reads for a card: each face's type line and rules text, faces joined in order."""
from dataclasses import dataclass

from archetype_classifier.card_embeddings.pool import Card


@dataclass(frozen=True)
class TextRecipe:
    stats: bool = False  # Put the mana cost and stats before the type line.
    mask: bool = False  # Replace the face's own name with ~.

BASE = TextRecipe()


def build_card_text(card: Card, recipe: TextRecipe) -> str:
    face = card.faces[0]
    return f'{face.type_line}\n{face.oracle_text}'
