"""The text an encoder reads for a card, in one of several formats.

- base: each face's type line and rules text (stage 1).
- stats: each face's mana cost, type line and stats on one line ('{R}{R} Creature — Human Assassin 2/2'), then its rules text.
- labels: the same with each field named ('Cost: {R}{R} Type: Creature — Human Assassin Power: 2 Toughness: 2'), then its rules text.
- json: a JSON object with labelled fields (manaCost, type, text, power, toughness, loyalty), a field the face lacks left out; a card with several faces
  is {"layout": ..., "faces": [...]}. Like minimaxir's mtg-embeddings, without name, rarity or sets.

Text formats join faces with a line holding //. Reminder text is always kept, and a cost or stat a face lacks is always left out. Masking writes a face's
own name in its rules text as ~ (agreed formats 2026-10-05, #7).
"""
import json
import re
from dataclasses import dataclass
from typing import Literal

from archetype_classifier.card_embeddings.pool import Card, Face

Style = Literal['plain', 'stats', 'labels', 'json']


@dataclass(frozen=True)
class TextRecipe:
    style: Style = 'plain'
    mask: bool = False  # Replace each face's own name in its rules text with ~.

    @property
    def label(self) -> str:
        """For file names and reports: 'base', 'masked', 'stats', 'labels', 'json' or 'json+masked'."""
        name = 'base' if self.style == 'plain' else self.style
        if not self.mask:
            return name
        return 'masked' if self.style == 'plain' else f'{name}+masked'

TEXT_VERSION = 2  # Bump whenever a recipe's output changes, so old embeddings aren't mistaken for new ones. 2: the stats format lost its ' · '.
BASE = TextRecipe()
MASKED = TextRecipe(mask=True)
STATS = TextRecipe('stats')
LABELS = TextRecipe('labels')
JSON = TextRecipe('json')
JSON_MASKED = TextRecipe('json', mask=True)
RECIPES = {r.label: r for r in (BASE, MASKED, STATS, LABELS, JSON, JSON_MASKED)}
MASK = '~'
FACE_SEPARATOR = '\n//\n'


def build_card_text(card: Card, recipe: TextRecipe) -> str:
    if recipe.style == 'json':
        faces = [face_fields(face, recipe) for face in card.faces]
        return json.dumps(faces[0] if len(faces) == 1 else {'layout': card.layout, 'faces': faces}, indent=2, ensure_ascii=False)
    return FACE_SEPARATOR.join(face_text(face, recipe) for face in card.faces)

def face_text(face: Face, recipe: TextRecipe) -> str:
    header = {'plain': face.type_line, 'stats': stats_line(face), 'labels': labels_line(face)}[recipe.style]
    return '\n'.join(part for part in (header, rules_text(face, recipe)) if part)

def face_fields(face: Face, recipe: TextRecipe) -> dict[str, str]:
    fields = {'manaCost': face.mana_cost, 'type': face.type_line, 'text': rules_text(face, recipe), 'power': face.power, 'toughness': face.toughness,
              'loyalty': face.loyalty}
    return {k: v for k, v in fields.items() if v}

def rules_text(face: Face, recipe: TextRecipe) -> str:
    return build_masked_text(face)[0] if recipe.mask else face.oracle_text

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
    """Mana cost, type line and stats, leaving out any the face doesn't have: '{U}{U} Creature — Beast 1/4'. Loyalty is a bare number, implied by the type."""
    stats = f'{face.power}/{face.toughness}' if face.power is not None and face.toughness is not None else None
    return ' '.join(part for part in (face.mana_cost, face.type_line, stats, face.loyalty) if part)

def labels_line(face: Face) -> str:
    """Each field named with a colon, leaving out any the face doesn't have: 'Cost: {R}{R} Type: Creature — Human Assassin Power: 2 Toughness: 2'."""
    fields = (('Cost', face.mana_cost), ('Type', face.type_line), ('Power', face.power), ('Toughness', face.toughness), ('Loyalty', face.loyalty))
    return ' '.join(f'{name}: {value}' for name, value in fields if value)
