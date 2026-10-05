"""The card pool: every card ever legal in Penny Dreadful, with its faces in order."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Face:
    name: str
    mana_cost: str
    cmc: float
    type_line: str
    oracle_text: str
    power: str | None = None
    toughness: str | None = None
    loyalty: str | None = None

@dataclass(frozen=True)
class Card:
    name: str  # The site's name: "A // B" for split cards, otherwise the front face's name.
    layout: str
    faces: tuple[Face, ...]  # In position order.
    seasons: frozenset[int] = frozenset()  # The seasons it was legal in.
