"""The text an encoder reads for a card: each face's type line and rules text, faces joined in order."""
import re
from dataclasses import dataclass

from archetype_classifier.card_embeddings.pool import Card, Face


@dataclass(frozen=True)
class TextRecipe:
    stats: bool = False  # Put the mana cost and stats before the type line.
    mask: bool = False  # Replace the face's own name with ~.

TEXT_VERSION = 1  # Bump whenever a recipe's output changes, so old embeddings aren't mistaken for new ones.
BASE = TextRecipe()
STATS = TextRecipe(stats=True)
MASKED = TextRecipe(mask=True)
MASK = '~'
FACE_SEPARATOR = '\n//\n'


def build_card_text(card: Card, recipe: TextRecipe) -> str:
    return FACE_SEPARATOR.join(face_text(face, recipe) for face in card.faces)

def face_text(face: Face, recipe: TextRecipe) -> str:
    header = stats_line(face) if recipe.stats else face.type_line
    rules = build_masked_text(face)[0] if recipe.mask else face.oracle_text
    return '\n'.join(part for part in (header, rules) if part)

def build_masked_text(face: Face) -> tuple[str, tuple[str, ...]]:
    """The face's rules text with its own name written as ~, and the short names it masked beyond the full name, for the spot-check.

    The full name and, on a legendary, the part before the comma are matched case-sensitively as whole words."""
    text = whole_word(face.name).sub(MASK, face.oracle_text)
    short = face.name.split(',')[0]
    if 'Legendary' not in face.type_line or short == face.name or not whole_word(short).search(text):
        return text, ()
    return whole_word(short).sub(MASK, text), (short,)

def whole_word(name: str) -> re.Pattern[str]:
    return re.compile(rf'(?<!\w){re.escape(name)}(?!\w)')

def stats_line(face: Face) -> str:
    """The type line with the mana cost before it and the stats after it, leaving out any the face doesn't have: '{U}{U} · Creature — Beast · 1/4'."""
    stats = f'{face.power}/{face.toughness}' if face.power is not None and face.toughness is not None else None
    loyalty = f'Loyalty {face.loyalty}' if face.loyalty is not None else None
    return ' · '.join(part for part in (face.mana_cost, face.type_line, stats, loyalty) if part)
