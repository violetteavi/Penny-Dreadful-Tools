"""The structured vector: a card's cost, types and stats as numbers, one block per face plus its layout.

A stat a face doesn't have is absent (present 0), never a 0 value: a sorcery's power isn't a 0-power creature's. Defense is left out until the cards import
stores it (#38); produced mana is a candidate for #36.
"""
import logging
import re

import numpy as np

from archetype_classifier.card_embeddings.pool import Card, Face
from magic import layout, mana

logger = logging.getLogger(__name__)

COLOURS = ('W', 'U', 'B', 'R', 'G', 'C', 'S')  # S is snow mana, which magic.mana parses as a colour.
SUPERTYPES = ('Basic', 'Legendary', 'Snow', 'World')
TYPES = ('Artifact', 'Battle', 'Creature', 'Enchantment', 'Instant', 'Kindred', 'Land', 'Planeswalker', 'Sorcery')
STATS = ('power', 'toughness', 'loyalty')
MAX_STAT = 15  # Larger values are clipped: a 20/20 reads as 15/15.
LAYOUTS = tuple(sorted(layout.playable_layouts()))
BLOCK = ('mana_value', 'generic', 'x', 'hybrid', 'phyrexian', *(f'pips.{c}' for c in COLOURS), *(f'supertype.{s}' for s in SUPERTYPES),
         *(f'type.{t}' for t in TYPES), *(f'{s}.{part}' for s in STATS for part in ('present', 'value', 'variable')))
STRUCTURED_COLUMNS = (*(f'front.{c}' for c in BLOCK), *(f'back.{c}' for c in BLOCK), *(f'layout.{lo}' for lo in LAYOUTS))


def build_structured_vector(card: Card) -> np.ndarray:
    if len(card.faces) > 2:
        logger.warning('%s has %d faces; the structured vector uses the first two', card.name, len(card.faces))
    back = face_block(card.faces[1]) if len(card.faces) > 1 else [0.0] * len(BLOCK)
    layouts = [float(card.layout == lo) for lo in LAYOUTS]
    return np.array([*face_block(card.faces[0]), *back, *layouts], dtype=np.float32)

def face_block(face: Face) -> list[float]:
    values = dict.fromkeys(BLOCK, 0.0)
    values['mana_value'] = face.cmc
    for symbol in mana.parse(face.mana_cost):
        if mana.generic(symbol):
            values['generic'] += int(symbol)
        elif mana.variable(symbol):
            values['x'] += 1
        else:
            values['hybrid'] += mana.hybrid(symbol) or mana.twobrid(symbol)
            values['phyrexian'] += symbol.endswith('/P')
            for colour in {c for c in symbol.split('/') if c in COLOURS}:  # Each colour that can pay for the symbol.
                values[f'pips.{colour}'] += 1
    kinds = face.type_line.split('—')[0].replace('Tribal', 'Kindred').split()
    for word in kinds:
        if word in SUPERTYPES:
            values[f'supertype.{word}'] = 1
        if word in TYPES:
            values[f'type.{word}'] = 1
    for name in STATS:
        raw = getattr(face, name)
        if raw is not None:
            number = re.match(r'-?\d+', raw)
            values[f'{name}.present'] = 1
            values[f'{name}.value'] = min(int(number.group()), MAX_STAT) if number else 0
            values[f'{name}.variable'] = float('*' in raw or 'X' in raw)
    return list(values.values())
