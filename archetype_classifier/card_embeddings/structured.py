"""A card's numbers: mana value, power, toughness and loyalty as (present, variable, fixed), and its colours, for comparing cards on their numbers.

Each scalar is (present, variable, fixed): present when the face prints it (for mana value, when it has a mana cost), variable when it holds * or X, and
fixed the number written in it (X and * count 0). A stat a face doesn't have is absent, never a 0 value: a sorcery's power isn't a 0-power creature's.
Numbers come from the front face, as the rules do off the stack, except that a split card's mana value is the sum of both halves and its colours both
halves' (#40 revisits this). Hybrid and Phyrexian symbols count towards each of their colours. Defense waits for the cards import to store it (#38).
"""
import re
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from archetype_classifier.card_embeddings.pool import Card
from magic import mana

WUBRG = ('W', 'U', 'B', 'R', 'G')

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
