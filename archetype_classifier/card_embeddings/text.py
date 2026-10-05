"""The text an encoder reads for a card: each face's type line and rules text, faces joined in order."""
from dataclasses import dataclass

from archetype_classifier.card_embeddings.pool import Card, Face


@dataclass(frozen=True)
class TextRecipe:
    stats: bool = False  # Put the mana cost and stats before the type line.
    mask: bool = False  # Replace the face's own name with ~.

BASE = TextRecipe()
FACE_SEPARATOR = '\n//\n'


def build_card_text(card: Card, recipe: TextRecipe) -> str:
    return FACE_SEPARATOR.join(face_text(face) for face in card.faces)

def face_text(face: Face) -> str:
    return '\n'.join(part for part in (face.type_line, face.oracle_text) if part)
