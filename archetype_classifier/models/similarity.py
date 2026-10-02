"""The similarity baseline: today's guesser, reimplemented with sparse matrices.

A deck is compared with every training deck that shares a non-basic maindeck card. The score is the summed weights of the maindeck lines both decks
share (same card and quantity), divided by the larger deck total, as a rounded whole percentage. Each card weighs 1 / max(playability, 0.001), with
playability computed by the site's formula from the training decks only. A League deck copies the label of its best match that is reviewed and
labelled; a Gatherling deck copies the label of its single top match. A match must reach the threshold, or the deck gets no guess.
"""
from collections import Counter, defaultdict
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from typing import ClassVar, cast

import numpy as np
from scipy import sparse

from archetype_classifier.evaluation.model import JSON, FitContext, LabelledDeck, PredictDeck, Prediction, TrainingDeck, register

FLOOR = 0.001  # The lowest playability a card weighs as: 1 / 0.001 = 1,000.
SIDEBOARD_WEIGHT = 0.2  # A deck playing a card only in its sideboard counts as this much of a deck, as on the site.
BASIC_LANDS = frozenset({'Plains', 'Island', 'Swamp', 'Mountain', 'Forest'})  # Sharing only these doesn't make two decks candidates.
CHUNK = 2000  # Query decks scored at once.

@dataclass(frozen=True)
class Match:
    deck_id: int
    score: int  # A whole percentage, as the site rounds it.


@register
class SimilarityBaseline:
    name: ClassVar[str] = 'similarity'
    version: ClassVar[int] = 1

    def __init__(self, params: dict[str, JSON]) -> None:
        self.params = params
        self.playability: dict[str, float] = {}

    def fit(self, training: Sequence[TrainingDeck], validation: Sequence[LabelledDeck], context: FitContext) -> None:
        self.playability = playability(training, context.legal_cards)
        self.threshold = cast(int, self.params['threshold'])
        self.index = Index(training, self.weight)

    def matches(self, deck: PredictDeck) -> list[Match]:
        """Every candidate training deck, best first: by score, then by higher deck id (roughly, most recent)."""
        ids, scores = next(self.index.scores([deck]))
        order = np.lexsort((-self.index.deck_ids[ids], -scores))
        return [Match(int(self.index.deck_ids[ids[k]]), int(scores[k])) for k in order]

    def weight(self, card: str) -> float:
        return 1.0 / max(self.playability.get(card, FLOOR), FLOOR)

    def predict(self, decks: Sequence[PredictDeck]) -> list[Prediction]:
        predictions = []
        for deck, (ids, scores) in zip(decks, self.index.scores(decks)):
            eligible = self.index.reviewed[ids] & (self.index.labels[ids] >= 0)
            best = best_match(ids[eligible], scores[eligible], self.index.deck_ids)
            if best is None or scores[eligible][best] < self.threshold:
                predictions.append(Prediction(deck.deck_id, None, {}))
                continue
            row = ids[eligible][best]
            predictions.append(Prediction(deck.deck_id, int(self.index.labels[row]), {'match_deck_id': int(self.index.deck_ids[row]), 'score': int(scores[eligible][best]), 'rule': 'league'}))
        return predictions

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


class Index:
    """The training decks as sparse matrices: maindeck lines (card and quantity) and non-basic card names, one row per deck."""
    def __init__(self, training: Sequence[TrainingDeck], weight: Callable[[str], float]) -> None:
        self.weight = weight
        self.deck_ids = np.array([d.deck.deck_id for d in training])
        self.labels = np.array([-1 if d.archetype_id is None else d.archetype_id for d in training])
        self.reviewed = np.array([d.reviewed for d in training], dtype=bool)
        self.lines: dict[tuple[str, int], int] = {}
        self.names: dict[str, int] = {}
        line_rows, line_cols, name_rows, name_cols = [], [], [], []
        for row, d in enumerate(training):
            for c in d.deck.maindeck:
                line_rows.append(row)
                line_cols.append(self.lines.setdefault((c.card, c.n), len(self.lines)))
                if c.card not in BASIC_LANDS:
                    name_rows.append(row)
                    name_cols.append(self.names.setdefault(c.card, len(self.names)))
        self.line_weights = np.array([weight(card) for card, _ in self.lines])
        self.training_lines = sparse.csr_matrix((np.ones(len(line_rows)), (line_rows, line_cols)), shape=(len(training), len(self.lines))).T.tocsr()
        self.training_names = sparse.csr_matrix((np.ones(len(name_rows)), (name_rows, name_cols)), shape=(len(training), len(self.names))).T.tocsr()
        self.totals = np.array([sum(weight(c.card) for c in d.deck.maindeck) for d in training])

    def scores(self, decks: Sequence[PredictDeck]) -> Iterator[tuple[np.ndarray, np.ndarray]]:
        """For each deck, its candidate training rows and their scores, a chunk of decks at a time."""
        for start in range(0, len(decks), CHUNK):
            chunk = decks[start:start + CHUNK]
            query_lines = self.encode(chunk, lambda c: self.lines.get((c.card, c.n)), self.line_weights)
            query_names = self.encode(chunk, lambda c: self.names.get(c.card) if c.card not in BASIC_LANDS else None, None)
            shared = (query_lines @ self.training_lines).tocsr()
            candidates = (query_names @ self.training_names).tocsr()
            for i, deck in enumerate(chunk):
                rows = candidates.indices[candidates.indptr[i]:candidates.indptr[i + 1]]
                weights = np.zeros(len(self.deck_ids))
                weights[shared.indices[shared.indptr[i]:shared.indptr[i + 1]]] = shared.data[shared.indptr[i]:shared.indptr[i + 1]]
                total = sum(self.weight(c.card) for c in deck.maindeck)  # Its unseen lines count here, though nothing can share them.
                yield rows, np.round(weights[rows] / np.maximum(total, self.totals[rows]) * 100).astype(int)

    def encode(self, decks: Sequence[PredictDeck], column: Callable[..., int | None], weights: np.ndarray | None) -> sparse.csr_matrix:
        rows, cols, data = [], [], []
        for row, d in enumerate(decks):
            for c in d.maindeck:
                col = column(c)
                if col is not None:
                    rows.append(row)
                    cols.append(col)
                    data.append(1.0 if weights is None else weights[col])
        return sparse.csr_matrix((data, (rows, cols)), shape=(len(decks), len(weights) if weights is not None else len(self.names)))

def best_match(rows: np.ndarray, scores: np.ndarray, deck_ids: np.ndarray) -> int | None:
    """The position of the best match among the given rows: highest score, then higher deck id."""
    if len(rows) == 0:
        return None
    return int(np.lexsort((-deck_ids[rows], -scores))[0])
