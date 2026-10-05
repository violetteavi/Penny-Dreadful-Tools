"""The card pool: every card ever legal in Penny Dreadful, with its faces in order.

A card's name and layout come from the site (magic.oracle), so names match decklists and legality. Its faces are read from the cards database's face
table in position order: the site's merged card drops the back face's type line and stats, and joins the faces' text in no fixed order (#39).
"""
import logging
from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from archetype_classifier.data_loading import loader
from magic import layout, oracle, seasons
from magic.database import db

logger = logging.getLogger(__name__)


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

@dataclass(frozen=True)
class SiteCard:
    card_id: int
    name: str
    layout: str


def load_card_pool() -> list[Card]:
    by_season = loader.load_legal_cards(range(1, seasons.current_season_num() + 1))
    legal: dict[str, set[int]] = defaultdict(set)
    for season_id, names in by_season.items():
        for name in names:
            legal[name].add(season_id)
    site_cards = [SiteCard(c.id, c.name, c.layout) for c in oracle.load_cards()]
    return build_card_pool({n: frozenset(s) for n, s in legal.items()}, site_cards, load_faces())

def load_faces() -> dict[int, tuple[Face, ...]]:
    """Every card's faces, in position order, keyed by card id."""
    faces: dict[int, list[Face]] = defaultdict(list)
    sql = 'SELECT card_id, name, mana_cost, cmc, type_line, oracle_text, power, toughness, loyalty FROM face ORDER BY card_id, position'
    for r in db().select(sql):
        faces[r['card_id']].append(Face(r['name'], r['mana_cost'] or '', r['cmc'] or 0.0, r['type_line'], r['oracle_text'], r['power'], r['toughness'], r['loyalty']))  # type: ignore[index, arg-type]
    return {card_id: tuple(f) for card_id, f in faces.items()}

def build_card_pool(legal: Mapping[str, frozenset[int]], site_cards: Iterable[SiteCard], faces: Mapping[int, tuple[Face, ...]]) -> list[Card]:
    """The legal cards in a playable layout, in name order. A legal name the cards database lacks is skipped with a warning."""
    by_name = {c.name: c for c in site_cards}
    missing = sorted(n for n in legal if n not in by_name)
    if missing:
        logger.warning('Skipped %d legal card%s the cards database lacks: %s', len(missing), '' if len(missing) == 1 else 's', ', '.join(missing))
    pool = [Card(name, by_name[name].layout, faces[by_name[name].card_id], seasons_legal) for name, seasons_legal in legal.items()
            if name in by_name and layout.is_playable_layout(by_name[name].layout)]
    return sorted(pool, key=lambda c: c.name)
