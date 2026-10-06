"""The structured vector: a card's cost, types and stats as numbers, one block per face plus its layout.

Three schemes (#7, 2026-10-05):
- current: mana value; generic, X, hybrid and Phyrexian counts; pips per colour; types and supertypes; each stat as present, value (clipped at 15)
  and variable; layout.
- log: mana value and stat values as log(max(1, 1 + value)), so 2 to 4 is about as far as 4 to 8 and a negative value counts as 0; colours as five
  yes/no columns (W U B R G) from the mana cost, hybrid and Phyrexian symbols counting towards their colours; types, supertypes and layout as current.
- numbers: log without types, supertypes and layout, which the card's text already carries.

A stat a face doesn't have is absent (present 0), never a 0 value: a sorcery's power isn't a 0-power creature's. Defense is left out until the cards import
stores it (#38); produced mana is a candidate for #36.
"""
import logging
import math
import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

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
Scheme = Literal['current', 'log', 'numbers']
WUBRG = ('W', 'U', 'B', 'R', 'G')
STAT_PARTS = tuple(f'{s}.{part}' for s in STATS for part in ('present', 'value', 'variable'))
TYPE_PARTS = (*(f'supertype.{s}' for s in SUPERTYPES), *(f'type.{t}' for t in TYPES))
NUMBERS_BLOCK = ('mana_value', *(f'colour.{c}' for c in WUBRG), *STAT_PARTS)
LOG_BLOCK = ('mana_value', *(f'colour.{c}' for c in WUBRG), *TYPE_PARTS, *STAT_PARTS)


def structured_columns(scheme: Scheme = 'current') -> tuple[str, ...]:
    if scheme == 'current':
        return STRUCTURED_COLUMNS
    block = LOG_BLOCK if scheme == 'log' else NUMBERS_BLOCK
    layouts = tuple(f'layout.{lo}' for lo in LAYOUTS) if scheme == 'log' else ()
    return (*(f'front.{c}' for c in block), *(f'back.{c}' for c in block), *layouts)


def build_structured_vector(card: Card, scheme: Scheme = 'current') -> np.ndarray:
    if len(card.faces) > 2:
        logger.warning('%s has %d faces; the structured vector uses the first two', card.name, len(card.faces))
    if scheme == 'current':
        build, size, layouts = face_block, len(BLOCK), [float(card.layout == lo) for lo in LAYOUTS]
    else:
        block = LOG_BLOCK if scheme == 'log' else NUMBERS_BLOCK
        build, size = (lambda face: log_face_block(face, block)), len(block)
        layouts = [float(card.layout == lo) for lo in LAYOUTS] if scheme == 'log' else []
    back = build(card.faces[1]) if len(card.faces) > 1 else [0.0] * size
    return np.array([*build(card.faces[0]), *back, *layouts], dtype=np.float32)

def log_scale(value: float) -> float:
    return math.log(max(1.0, 1.0 + value))

def log_face_block(face: Face, block: tuple[str, ...]) -> list[float]:
    """A face's columns in the log and numbers schemes, in the block's order; a column the block lacks is dropped."""
    values = dict.fromkeys(block, 0.0)
    values['mana_value'] = log_scale(face.cmc)  # The face's mana value already counts X as 0.
    for symbol in mana.parse(face.mana_cost):
        for colour in set(symbol.split('/')) & set(WUBRG):
            values[f'colour.{colour}'] = 1
    for word in face.type_line.split('—')[0].replace('Tribal', 'Kindred').split():
        for column in (f'supertype.{word}', f'type.{word}'):
            if column in values:
                values[column] = 1
    for name in STATS:
        raw = getattr(face, name)
        if raw is not None:
            number = re.match(r'-?\d+', raw)
            values[f'{name}.present'] = 1
            values[f'{name}.value'] = log_scale(int(number.group()) if number else 0)
            values[f'{name}.variable'] = float('*' in raw or 'X' in raw)
    return list(values.values())

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


# Front-face numbers for stage 2d (#7 spec, 2026-10-05). Each scalar is (present, variable, fixed): present when the face prints it (for mana value, when
# it has a mana cost), variable when it holds * or X, and fixed the number written in it (X and * count 0). A split card's mana value is the sum of
# both halves and its colours both halves'; every other card uses its front face, as the rules do off the stack (#40 revisits this).

SCALARS = ('mana_value', 'power', 'toughness', 'loyalty')


@dataclass(frozen=True)
class Scalar:
    present: bool
    variable: bool
    fixed: float
    sign: int = 1  # Minus 1 when the variable part is subtracted, as in 7-*.

ABSENT = Scalar(False, False, 0)


@dataclass(frozen=True)
class CardNumbers:
    mana_value: Scalar
    power: Scalar
    toughness: Scalar
    loyalty: Scalar
    colours: frozenset[str]


@dataclass(frozen=True)
class FrontNumbers:
    """Every card's numbers as arrays, one row per card and one column per scalar (SCALARS order); colours in W U B R G order."""
    names: tuple[str, ...]
    present: np.ndarray
    variable: np.ndarray
    fixed: np.ndarray
    sign: np.ndarray
    colours: np.ndarray

    def log_values(self) -> np.ndarray:
        """log(max(1, 1 + fixed)): 2 to 4 is about as far as 4 to 8, and anything at or below 0 counts as 0."""
        return np.log(np.maximum(1.0, 1.0 + self.fixed))


def build_card_numbers(card: Card) -> CardNumbers:
    faces = card.faces if card.layout == 'split' else card.faces[:1]
    costs = [f.mana_cost for f in faces if f.mana_cost]
    mana_value = Scalar(True, any('{X}' in c for c in costs), sum(mana.cmc(c) for c in costs)) if costs else ABSENT
    colours = frozenset(c for cost in costs for symbol in mana.parse(cost) for c in symbol.split('/') if c in WUBRG)
    front = card.faces[0]
    return CardNumbers(mana_value, parse_scalar(front.power), parse_scalar(front.toughness), parse_scalar(front.loyalty), colours)

def parse_scalar(raw: str | None) -> Scalar:
    if raw is None:
        return ABSENT
    number = re.search(r'-?\d+', raw)
    variable = '*' in raw or 'X' in raw
    sign = -1 if re.search(r'-\s*[*X]', raw) else 1
    return Scalar(True, variable, int(number.group()) if number else 0, sign)

def build_front_numbers(cards: Sequence[Card]) -> FrontNumbers:
    numbers = [build_card_numbers(c) for c in cards]
    scalars = [[getattr(n, s) for s in SCALARS] for n in numbers]
    return FrontNumbers(tuple(c.name for c in cards),
                        np.array([[x.present for x in row] for row in scalars], dtype=bool),
                        np.array([[x.variable for x in row] for row in scalars], dtype=bool),
                        np.array([[x.fixed for x in row] for row in scalars], dtype=np.float64),
                        np.array([[x.sign for x in row] for row in scalars], dtype=np.float64),
                        np.array([[float(c in n.colours) for c in WUBRG] for n in numbers], dtype=np.float64))
