"""Card weights (#50; Scenarios.md, "Deck representations"): how much each card counts in a deck's representation, as a legality-aware IDF.

    IDF(c) = ln((1 + N_c) / (1 + df_c)) + 1

N_c is the number of training decks in the training seasons where card c is legal, and df_c is how many of them play c in their maindeck, once per deck
whatever its copies. Every training deck counts, repeats included: IDF measures how often a card is played. Sideboards don't count. A card played in a
season whose legal list lacks it counts that season as legal, with one warning (a data gap, never fatal). A card never legal in a training season weighs
as an unplayed card from one average season, ln(1 + training decks / training seasons) + 1.
"""
import hashlib
import logging
import math
from collections import Counter, defaultdict
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

from archetype_classifier.evaluation.model import JSON, TrainingDeck

logger = logging.getLogger(__name__)

BASIC_LANDS = ('Plains', 'Island', 'Swamp', 'Mountain', 'Forest')
NAMED_OUTSIDE = 5  # The most-played cards the warning names.
COPIES: dict[str, Callable[[int], float]] = {'linear': float, 'sqrt': math.sqrt}  # copies(n): how a maindeck line's copies count.


@dataclass(frozen=True)
class CardWeights:
    idf: Mapping[str, float]  # Every card legal in a training season or played by a training deck.
    never_legal: float
    outside_legal: tuple[str, ...]  # Cards played in a season whose legal list lacks them, most played first.

    def weight(self, card: str) -> float:
        return self.idf.get(card, self.never_legal)

    def hash(self) -> str:
        """The weights to 6 decimals, so a model can refuse to load on different ones."""
        text = ';'.join(f'{card}:{w:.6f}' for card, w in sorted(self.idf.items())) + f';never legal:{self.never_legal:.6f}'
        return hashlib.sha1(text.encode()).hexdigest()

    def summary(self) -> dict[str, JSON]:
        """What a model's state records about its weights: never the table, which the training decks and legality rebuild."""
        return {'cards': len(self.idf), 'never_legal_weight': round(self.never_legal, 4),
                'basic_lands': {land: round(self.idf[land], 4) for land in BASIC_LANDS if land in self.idf},
                'played_outside_legal_seasons': list(self.outside_legal), 'card_weights_hash': self.hash()}


def build_card_weights(training: Sequence[TrainingDeck], legal_cards: Mapping[int, frozenset[str]]) -> CardWeights:
    decks_per_season = Counter(d.season_id for d in training)
    played = Counter[str]()
    played_in: defaultdict[str, set[int]] = defaultdict(set)
    for d in training:
        for card in {line.card for line in d.deck.maindeck}:
            played[card] += 1
            played_in[card].add(d.season_id)
    seasons: defaultdict[str, set[int]] = defaultdict(set)
    for season_id, cards in legal_cards.items():
        if season_id in decks_per_season:
            for card in cards:
                seasons[card].add(season_id)
    outside = tuple(sorted((c for c in played if played_in[c] - seasons[c]), key=lambda c: (-played[c], c)))
    if outside:
        logger.warning('%d card%s played outside %s legal seasons, counted as legal there; most played: %s', len(outside), '' if len(outside) == 1 else 's',
                       'its' if len(outside) == 1 else 'their', ', '.join(outside[:NAMED_OUTSIDE]))
    idf = {c: math.log((1 + sum(decks_per_season[s] for s in seasons[c] | played_in[c])) / (1 + played[c])) + 1 for c in set(seasons) | set(played)}
    never_legal = math.log(1 + len(training) / len(decks_per_season)) + 1 if decks_per_season else 1.0
    return CardWeights(idf, never_legal, outside)
