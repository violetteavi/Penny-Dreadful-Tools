"""The text an encoder reads for a card: each face's type line and rules text, faces joined by a line holding //.

Two formats: base (Scryfall's oracle text as it stands) and masked (each face's own name in its rules text written as ~, so functional reprints that
name themselves read the same). Reminder text is always kept. The formats tried and dropped in #7 (cost and stats in the text, inline labels, JSON) are
on the tag card-encoder-exploration.
"""
import re
from dataclasses import dataclass
from typing import Literal

from archetype_classifier.card_embeddings.pool import Card, Face

Style = Literal['plain']  # Kept as a field so saved manifests read {'style': 'plain', 'mask': ...}, as they did when there were other styles.
ARCHIVE_TAG = 'card-encoder-exploration'


@dataclass(frozen=True)
class TextRecipe:
    style: Style = 'plain'
    mask: bool = False  # Replace each face's own name in its rules text with ~.

    def __post_init__(self) -> None:
        if self.style != 'plain':
            raise ValueError(f"The '{self.style}' format was removed after #7; it is on the tag {ARCHIVE_TAG}")

    @property
    def label(self) -> str:
        """For file names and reports: 'base' or 'masked'."""
        return 'masked' if self.mask else 'base'

TEXT_VERSION = 2  # Bump whenever a recipe's output changes, so old embeddings aren't mistaken for new ones. Base and masked text are as in version 2.
BASE = TextRecipe()
MASKED = TextRecipe(mask=True)
RECIPES = {r.label: r for r in (BASE, MASKED)}
MASK = '~'
FACE_SEPARATOR = '\n//\n'


def build_card_text(card: Card, recipe: TextRecipe) -> str:
    return FACE_SEPARATOR.join(face_text(face, recipe) for face in card.faces)

def face_text(face: Face, recipe: TextRecipe) -> str:
    rules = build_masked_text(face)[0] if recipe.mask else face.oracle_text
    return '\n'.join(part for part in (face.type_line, rules) if part)

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
