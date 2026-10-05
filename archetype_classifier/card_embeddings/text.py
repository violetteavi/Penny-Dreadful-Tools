"""The text an encoder reads for a card: each face's type line and rules text, faces joined in order."""
from dataclasses import dataclass

from archetype_classifier.card_embeddings.pool import Card, Face


@dataclass(frozen=True)
class TextRecipe:
    stats: bool = False  # Put the mana cost and stats before the type line.
    mask: bool = False  # Replace the face's own name with ~.

BASE = TextRecipe()
STATS = TextRecipe(stats=True)
FACE_SEPARATOR = '\n//\n'


def build_card_text(card: Card, recipe: TextRecipe) -> str:
    return FACE_SEPARATOR.join(face_text(face, recipe) for face in card.faces)

def face_text(face: Face, recipe: TextRecipe) -> str:
    header = stats_line(face) if recipe.stats else face.type_line
    return '\n'.join(part for part in (header, face.oracle_text) if part)

def stats_line(face: Face) -> str:
    """The type line with the mana cost before it and the stats after it, leaving out any the face doesn't have: '{U}{U} · Creature — Beast · 1/4'."""
    stats = f'{face.power}/{face.toughness}' if face.power is not None and face.toughness is not None else None
    loyalty = f'Loyalty {face.loyalty}' if face.loyalty is not None else None
    return ' · '.join(part for part in (face.mana_cost, face.type_line, stats, loyalty) if part)
