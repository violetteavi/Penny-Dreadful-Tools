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

from archetype_classifier.evaluation.metrics import ArchetypeTree, overlap, sum_overlaps
from archetype_classifier.evaluation.model import JSON, FitContext, LabelledDeck, PredictDeck, Prediction, TrainingDeck, register

FLOOR = 0.001  # The lowest playability a card weighs as: 1 / 0.001 = 1,000.
SIDEBOARD_WEIGHT = 0.2  # A deck playing a card only in its sideboard counts as this much of a deck, as on the site.
BASIC_LANDS = frozenset({'Plains', 'Island', 'Swamp', 'Mountain', 'Forest'})  # Sharing only these doesn't make two decks candidates.
CHUNK = 2000  # Query decks scored at once.
SITE_THRESHOLD = 20  # The site's fixed threshold; a tuned threshold that ties breaks towards it.
THRESHOLDS = range(1, 101)

@dataclass(frozen=True)
class Match:
    deck_id: int
    score: int  # A whole percentage, as the site rounds it.

@dataclass(frozen=True)
class Pick:
    """The match a deck's label would be copied from, before the threshold is applied."""
    deck_id: int
    label_id: int
    score: int
    rule: str  # 'league' or 'gatherling'.


@register
class SimilarityBaseline:
    name: ClassVar[str] = 'similarity'
    version: ClassVar[int] = 1

    def __init__(self, params: dict[str, JSON]) -> None:
        self.params = params
        self.playability: dict[str, float] = {}

    def fit(self, training: Sequence[TrainingDeck], validation: Sequence[LabelledDeck], context: FitContext) -> None:
        self.playability = playability(training, context.legal_cards)
        self.index = Index(training, self.weight)
        self.curve = self.validation_curve(validation, context.tree)
        if self.params['threshold'] == 'tuned':
            if not self.curve:
                raise ValueError('A tuned threshold needs validation decks to tune on')
            best_hf = max(hf for _, _, _, hf in self.curve)
            self.threshold = min((t for t, _, _, hf in self.curve if hf == best_hf), key=lambda t: (abs(t - SITE_THRESHOLD), t))
        else:
            self.threshold = cast(int, self.params['threshold'])

    def validation_curve(self, validation: Sequence[LabelledDeck], tree: ArchetypeTree) -> list[tuple[int, float | None, float, float]]:
        """Micro hP, hR and hF on the validation decks at every whole-number threshold. Each deck's match is found once; a threshold only decides whether it's used."""
        if not validation:
            return []
        picks = [self.index.pick(d.deck.source, rows, scores) for d, (rows, scores) in zip(validation, self.index.scores([d.deck for d in validation]))]
        curve = []
        for threshold in THRESHOLDS:
            guesses = [p.label_id if p is not None and p.score >= threshold else None for p in picks]
            micro = sum_overlaps(overlap(tree, d.label_id, guess) for d, guess in zip(validation, guesses)).hierarchical()
            curve.append((threshold, micro.hp, micro.hr, micro.hf))
        return curve

    def matches(self, deck: PredictDeck) -> list[Match]:
        """Every candidate training deck, best first: by score, then by higher deck id (roughly, most recent)."""
        ids, scores = next(self.index.scores([deck]))
        order = np.lexsort((-self.index.deck_ids[ids], -scores))
        return [Match(int(self.index.deck_ids[ids[k]]), int(scores[k])) for k in order]

    def weight(self, card: str) -> float:
        return 1.0 / max(self.playability.get(card, FLOOR), FLOOR)

    def predict(self, decks: Sequence[PredictDeck]) -> list[Prediction]:
        predictions = []
        for deck, (rows, scores) in zip(decks, self.index.scores(decks)):
            pick = self.index.pick(deck.source, rows, scores)
            if pick is None or pick.score < self.threshold:
                predictions.append(Prediction(deck.deck_id, None, {}))
            else:
                predictions.append(Prediction(deck.deck_id, pick.label_id, {'match_deck_id': pick.deck_id, 'score': pick.score, 'rule': pick.rule}))
        return predictions

    def state(self) -> dict[str, JSON]:
        """What fitting learned: each card's playability (its weight is 1 / playability), the threshold, and the validation curve, as the Model protocol documents."""
        return {'playability': dict(self.playability), 'threshold': self.threshold, 'validation_curve': [list(point) for point in self.curve]}

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

    def pick(self, source: str, rows: np.ndarray, scores: np.ndarray) -> Pick | None:
        """As the site picks: a Gatherling deck copies its single top match, if labelled; any other deck its best reviewed, labelled match."""
        if source == 'Gatherling':
            best = best_match(rows, scores, self.deck_ids)
            if best is None or self.labels[rows[best]] < 0:
                return None
            return Pick(int(self.deck_ids[rows[best]]), int(self.labels[rows[best]]), int(scores[best]), 'gatherling')
        eligible = self.reviewed[rows] & (self.labels[rows] >= 0)
        best = best_match(rows[eligible], scores[eligible], self.deck_ids)
        if best is None:
            return None
        row = rows[eligible][best]
        return Pick(int(self.deck_ids[row]), int(self.labels[row]), int(scores[eligible][best]), 'league')

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
