"""The similarity baseline: today's guesser, reimplemented with sparse matrices.

A deck is compared with every training deck that shares a non-basic maindeck card. The score is the summed weights of the maindeck lines both decks
share (same card and quantity), divided by the larger deck total, as a rounded whole percentage. Each card weighs 1 / max(playability, 0.001), with
playability computed by the site's formula from the training decks only. A League deck copies the label of its best match that is reviewed and
labelled; a Gatherling deck copies the label of its single top match. A match must reach the threshold, or the deck gets no guess.
"""
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from typing import ClassVar

from archetype_classifier.evaluation.model import JSON, FitContext, LabelledDeck, PredictDeck, Prediction, TrainingDeck, register

FLOOR = 0.001  # The lowest playability a card weighs as: 1 / 0.001 = 1,000.
SIDEBOARD_WEIGHT = 0.2  # A deck playing a card only in its sideboard counts as this much of a deck, as on the site.


@register
class SimilarityBaseline:
    name: ClassVar[str] = 'similarity'
    version: ClassVar[int] = 1

    def __init__(self, params: dict[str, JSON]) -> None:
        self.params = params
        self.playability: dict[str, float] = {}

    def fit(self, training: Sequence[TrainingDeck], validation: Sequence[LabelledDeck], context: FitContext) -> None:
        self.playability = playability(training, context.legal_cards)

    def weight(self, card: str) -> float:
        return 1.0 / max(self.playability.get(card, FLOOR), FLOOR)

    def predict(self, decks: Sequence[PredictDeck]) -> list[Prediction]:
        raise NotImplementedError

    def state(self) -> dict[str, JSON]:
        raise NotImplementedError

    @classmethod
    def from_state(cls, params: dict[str, JSON], state: dict[str, JSON], training: Sequence[TrainingDeck], context: FitContext) -> 'SimilarityBaseline':
        raise NotImplementedError


def playability(training: Sequence[TrainingDeck], legal_cards: Mapping[int, frozenset[str]]) -> dict[str, float]:
    """The site's playability, from labelled training decks only, over the training seasons in which each card was legal. Rounded to 5 decimals, as the site stores it."""
    labelled = [d for d in training if d.archetype_id is not None]
    decks_per_season = Counter(d.season_id for d in labelled)
    in_maindeck: Counter[tuple[int, str]] = Counter()
    only_in_sideboard: Counter[tuple[int, str]] = Counter()
    for d in labelled:
        maindeck = {c.card for c in d.deck.maindeck}
        for card in maindeck:
            in_maindeck[(d.season_id, card)] += 1
        for card in {c.card for c in d.deck.sideboard} - maindeck:
            only_in_sideboard[(d.season_id, card)] += 1
    legal_seasons: dict[str, list[int]] = defaultdict(list)
    for season_id, cards in legal_cards.items():
        if season_id in decks_per_season:
            for card in cards:
                legal_seasons[card].append(season_id)
    return {card: round(sum(in_maindeck[(s, card)] + SIDEBOARD_WEIGHT * only_in_sideboard[(s, card)] for s in seasons) / sum(decks_per_season[s] for s in seasons), 5)
            for card, seasons in legal_seasons.items()}
