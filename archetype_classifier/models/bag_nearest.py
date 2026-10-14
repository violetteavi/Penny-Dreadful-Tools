"""The nearest deck on the bag of cards (#50; Scenarios.md, "Deck representations"): each maindeck as a sparse vector with copies(n) x the card's
weight at each card it plays, compared by cosine. Two different cards never match, however alike their text.

The vocabulary is every card the training rows play. A card outside it has no column, but it still counts in the deck's own length: it lowers the
deck's cosine with every row by the same factor, so it can't change the ranking, and the scores stay true cosines.
"""
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import ClassVar, cast

import numpy as np
from scipy import sparse

from archetype_classifier.data_loading.dataset import CardCount
from archetype_classifier.evaluation.model import JSON, FitContext, LabelledDeck, PredictDeck, Prediction, TrainingDeck, register
from archetype_classifier.models.card_weights import COPIES, build_card_weights
from archetype_classifier.models.embedding_nearest import build_candidates, build_pick, build_training_rows

CHUNK = 500  # Decks compared at once: an 84,000 x 500 float64 block is 340 MB. A sparse product would be nearly dense, and larger.


@dataclass(frozen=True)
class BagVectors:
    matrix: sparse.csr_matrix  # One unit-length row per deck over the vocabulary; empty for a deck with no known card.
    known: np.ndarray  # Maindeck copies in the vocabulary, per deck.
    unseen: np.ndarray  # Maindeck copies outside it, per deck.


def build_vocabulary(maindecks: Sequence[tuple[CardCount, ...]]) -> dict[str, int]:
    """Every card the maindecks play, as a column, in name order."""
    return {card: i for i, card in enumerate(sorted({line.card for maindeck in maindecks for line in maindeck}))}

def build_bag_vectors(maindecks: Sequence[tuple[CardCount, ...]], vocabulary: Mapping[str, int], weight: Callable[[str], float],
                      copies: Callable[[int], float]) -> BagVectors:
    rows, cols, values = [], [], []
    known = np.zeros(len(maindecks), dtype=np.int64)
    unseen = np.zeros(len(maindecks), dtype=np.int64)
    norms = np.zeros(len(maindecks))
    for row, maindeck in enumerate(maindecks):
        for line in maindeck:
            value = copies(line.n) * weight(line.card)
            norms[row] += value * value
            col = vocabulary.get(line.card)
            if col is None:
                unseen[row] += line.n
            else:
                rows.append(row)
                cols.append(col)
                values.append(value)
                known[row] += line.n
    lengths = np.sqrt(norms)
    scaled = [v / lengths[r] for r, v in zip(rows, values, strict=True)]
    matrix = sparse.csr_matrix((scaled, (rows, cols)), shape=(len(maindecks), len(vocabulary)), dtype=np.float64)
    return BagVectors(matrix, known, unseen)


@register
class BagNearestDeck:
    """Copies the label of the nearest training row on the bag of cards, with the nearest deck's rows, pick rule and candidates (Q2 of #50: only the
    representation differs). Card weights are always the legality-aware IDF; copies are linear or square root (the default)."""
    name: ClassVar[str] = 'bag of cards nearest deck'
    version: ClassVar[int] = 1

    def __init__(self, params: dict[str, JSON]) -> None:
        self.params = params
        self.copies = str(params.get('copies', 'sqrt'))
        if self.copies not in COPIES:
            raise ValueError(f'copies must be one of {tuple(COPIES)}, not {self.copies!r}')

    def fit(self, training: Sequence[TrainingDeck], validation: Sequence[LabelledDeck], context: FitContext) -> None:
        """Nothing is tuned, so the validation decks aren't used."""
        self.card_weights = build_card_weights(training, context.legal_cards)
        self.build_index(training)

    def build_index(self, training: Sequence[TrainingDeck]) -> None:
        self.training_decks = len(training)
        self.rows = build_training_rows(training)
        self.vocabulary = build_vocabulary(self.rows.maindecks)
        self.row_vectors = self.bag_vectors(self.rows.maindecks).matrix

    def bag_vectors(self, maindecks: Sequence[tuple[CardCount, ...]]) -> BagVectors:
        return build_bag_vectors(maindecks, self.vocabulary, self.card_weights.weight, COPIES[self.copies])

    def predict(self, decks: Sequence[PredictDeck]) -> list[Prediction]:
        predictions = []
        for start in range(0, len(decks), CHUNK):
            chunk = decks[start:start + CHUNK]
            vectors = self.bag_vectors([d.maindeck for d in chunk])
            similarities = (self.row_vectors @ vectors.matrix.T.toarray()).T  # Sparse rows times a dense block: never a near-dense sparse result.
            for i, deck in enumerate(chunk):
                counts: dict[str, JSON] = {'known_copies': int(vectors.known[i]), 'unseen_copies': int(vectors.unseen[i])}
                if not vectors.known[i]:
                    predictions.append(Prediction(deck.deck_id, None, counts, ()))
                    continue
                pick = build_pick(similarities[i], self.rows)
                evidence: dict[str, JSON] = {'match_deck_id': pick.deck_id, 'similarity': round(pick.similarity, 6), 'match_decks': pick.decks, 'tied_rows': pick.tied_rows,
                                             'runner_up_id': pick.runner_up_id,
                                             'runner_up_similarity': None if pick.runner_up_similarity is None else round(pick.runner_up_similarity, 6), **counts}
                predictions.append(Prediction(deck.deck_id, pick.label_id, evidence, build_candidates(similarities[i], self.rows)))
        return predictions

    def state(self) -> dict[str, JSON]:
        """Sizes and the card weights' summary; never vectors, which the training decks and legality rebuild."""
        return {'training_decks': self.training_decks, 'training_rows': len(self.rows.labels), 'vocabulary': len(self.vocabulary), 'card_weights': self.card_weights.summary()}

    @classmethod
    def from_state(cls, params: dict[str, JSON], state: dict[str, JSON], training: Sequence[TrainingDeck], context: FitContext) -> 'BagNearestDeck':
        """Rebuilds the card weights and rows, refusing weights that changed since fitting."""
        model = cls(params)
        model.card_weights = build_card_weights(training, context.legal_cards)
        fitted_hash = cast(dict[str, JSON], state['card_weights'])['card_weights_hash']
        if model.card_weights.hash() != fitted_hash:
            raise ValueError(f'The card weights have changed since the model was fitted: they were {fitted_hash}, they are now {model.card_weights.hash()}')
        model.build_index(training)
        return model
