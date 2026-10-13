"""The nearest deck on the combined embedding (#44): the similarity baseline's "copy the label of the best match", with each deck read as its deck
vector instead of its shared cards.

Training decks are grouped into training rows, one per distinct maindeck and label, so a list submitted many times is one piece of evidence. A deck
copies the label of the training row with the highest cosine similarity. Rows within TIE_TOLERANCE of the best are tied: among them the label with the
most decks wins, then the label whose newest deck is most recent. There's no archetype tree and no threshold: the model always guesses, unless none of
the deck's cards is in the embedding.

Its candidates (#14) are every label among the training rows, each ranked by its best row's similarity, which is also the candidate's score. Labels
within TIE_TOLERANCE of the first label of their group are tied, and ordered as the guess breaks ties: more decks among those rows, then the newer
deck. So candidate 1 is always the guess. Rows aren't summed: that's #45 and #50.
"""
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from typing import ClassVar, cast

import numpy as np

from archetype_classifier.card_embeddings.combined_embedding import load_combined_embedding, load_embedding_hash
from archetype_classifier.card_embeddings.deck_vectors import build_deck_vectors
from archetype_classifier.card_embeddings.text_embedding import EMBEDDINGS_DIR
from archetype_classifier.data_loading.dataset import CardCount
from archetype_classifier.evaluation.model import JSON, Candidate, FitContext, LabelledDeck, PredictDeck, Prediction, TrainingDeck, register

CHUNK = 1000  # Decks compared with every training row at once: a 1,000 x 84,000 float64 block is 670 MB.
SKIPPED_CARDS_KEPT = 20  # The most-skipped cards the state names.
TIE_TOLERANCE = 1e-9  # Rows this close to the best similarity are tied. Identical maindecks give exactly equal vectors, so they always tie.


@dataclass(frozen=True)
class Pick:
    label_id: int
    deck_id: int  # The newest deck behind the winning label among the tied rows.
    similarity: float  # The best row's cosine similarity.
    decks: int  # The winning label's decks among the tied rows.
    tied_rows: int
    runner_up_id: int | None  # The best other label, or None when every row has the guessed label.
    runner_up_similarity: float | None

@dataclass(frozen=True)
class TrainingRows:
    maindecks: tuple[tuple[CardCount, ...], ...]
    labels: np.ndarray
    deck_counts: np.ndarray
    newest_deck_ids: np.ndarray
    label_order: np.ndarray  # Row positions sorted by label, so each label's rows are one run...
    label_starts: np.ndarray  # ...starting at these positions in label_order: one per distinct label.


def build_training_rows(training: Sequence[TrainingDeck]) -> TrainingRows:
    """One row per distinct maindeck and label, in order of first appearance. A deck with no label is skipped."""
    rows: dict[tuple[tuple[CardCount, ...], int], list[int]] = {}  # (maindeck, label) -> [decks, newest deck id]
    for d in training:
        if d.archetype_id is None:
            continue
        row = rows.setdefault((d.deck.maindeck, d.archetype_id), [0, d.deck.deck_id])
        row[0] += 1
        row[1] = max(row[1], d.deck.deck_id)
    labels = np.array([label for _, label in rows], dtype=np.int64)
    order = np.argsort(labels, kind='stable')
    starts = np.flatnonzero(np.r_[True, labels[order][1:] != labels[order][:-1]]) if len(labels) else np.array([], dtype=np.int64)
    return TrainingRows(tuple(maindeck for maindeck, _ in rows), labels, np.array([n for n, _ in rows.values()], dtype=np.int64),
                        np.array([newest for _, newest in rows.values()], dtype=np.int64), order, starts)

def build_pick(similarities: np.ndarray, rows: TrainingRows) -> Pick:
    """The label to copy, from one deck's similarity to every training row (rows must not be empty)."""
    best = float(similarities.max())
    tied = np.flatnonzero(similarities >= best - TIE_TOLERANCE)
    decks: dict[int, int] = {}
    newest: dict[int, int] = {}
    for row in tied:
        label = int(rows.labels[row])
        decks[label] = decks.get(label, 0) + int(rows.deck_counts[row])
        newest[label] = max(newest.get(label, 0), int(rows.newest_deck_ids[row]))
    label = max(decks, key=lambda a: (decks[a], newest[a]))
    others = np.flatnonzero(rows.labels != label)
    runner_up = int(others[np.argmax(similarities[others])]) if len(others) else None
    return Pick(label, newest[label], best, decks[label], len(tied), None if runner_up is None else int(rows.labels[runner_up]),
                None if runner_up is None else float(similarities[runner_up]))


def build_candidates(similarities: np.ndarray, rows: TrainingRows) -> tuple[Candidate, ...]:
    """Every label, best first, by its best row's similarity. Labels within TIE_TOLERANCE of their group's first are ordered as build_pick orders them."""
    if not len(rows.labels):
        return ()
    labels = rows.labels[rows.label_order[rows.label_starts]]
    best = np.maximum.reduceat(similarities[rows.label_order], rows.label_starts)
    ranking = np.argsort(-best, kind='stable')
    ranked = best[ranking]
    group_starts = [0]
    for k in range(1, len(ranked)):
        if ranked[group_starts[-1]] - ranked[k] > TIE_TOLERANCE:
            group_starts.append(k)
    order: list[int] = []
    for start, end in zip(group_starts, [*group_starts[1:], len(ranked)], strict=True):
        group = ranking[start:end].tolist()
        if len(group) > 1:
            tied = similarities >= ranked[start] - TIE_TOLERANCE
            def popularity(g: int) -> tuple[int, int]:
                mine = tied & (rows.labels == labels[g])
                return int(rows.deck_counts[mine].sum()), int(rows.newest_deck_ids[mine].max())
            group.sort(key=popularity, reverse=True)
        order.extend(group)
    return tuple(Candidate(int(labels[g]), float(best[g])) for g in order)


@register
class EmbeddingNearestDeck:
    name: ClassVar[str] = 'embedding nearest deck'
    version: ClassVar[int] = 2  # 2: ranked candidates (#14).

    def __init__(self, params: dict[str, JSON]) -> None:
        self.params = params

    def fit(self, training: Sequence[TrainingDeck], validation: Sequence[LabelledDeck], context: FitContext) -> None:
        """Nothing is tuned, so the validation decks aren't used."""
        self.load_embedding(context)
        self.build_index(training)
        skipped = [(line.card, line.n * int(n)) for maindeck, n in zip(self.rows.maindecks, self.rows.deck_counts) for line in maindeck if line.card not in self.known]
        self.training_decks = len(training)
        self.skipped_copies = sum(copies for _, copies in skipped)
        self.decks_with_skipped_cards = int(self.rows.deck_counts[self.row_skipped > 0].sum())
        totals: Counter[str] = Counter()
        for card, copies in skipped:
            totals[card] += copies
        self.skipped_cards = dict(sorted(totals.items(), key=lambda item: (-item[1], item[0]))[:SKIPPED_CARDS_KEPT])

    def load_embedding(self, context: FitContext) -> None:
        path = (context.embeddings_dir or EMBEDDINGS_DIR) / f'{self.params["embedding"]}.npz'
        self.embedding = load_combined_embedding(path)
        self.embedding_hash = load_embedding_hash(path)
        self.known = frozenset(self.embedding.names)

    def build_index(self, training: Sequence[TrainingDeck]) -> None:
        self.rows = build_training_rows(training)
        vectors = build_deck_vectors(self.rows.maindecks, self.embedding)
        self.row_vectors, self.row_skipped = vectors.matrix, vectors.skipped

    def predict(self, decks: Sequence[PredictDeck]) -> list[Prediction]:
        predictions = []
        for start in range(0, len(decks), CHUNK):
            chunk = decks[start:start + CHUNK]
            vectors = build_deck_vectors([d.maindeck for d in chunk], self.embedding)
            similarities = vectors.matrix @ self.row_vectors.T
            for i, deck in enumerate(chunk):
                counts: dict[str, JSON] = {'embedded_copies': int(vectors.embedded[i]), 'skipped_copies': int(vectors.skipped[i])}
                if not vectors.embedded[i] or not len(self.rows.labels):
                    predictions.append(Prediction(deck.deck_id, None, counts, ()))
                    continue
                pick = build_pick(similarities[i], self.rows)
                evidence: dict[str, JSON] = {'match_deck_id': pick.deck_id, 'similarity': round(pick.similarity, 6), 'match_decks': pick.decks, 'tied_rows': pick.tied_rows,
                                             'runner_up_id': pick.runner_up_id,
                                             'runner_up_similarity': None if pick.runner_up_similarity is None else round(pick.runner_up_similarity, 6), **counts}
                predictions.append(Prediction(deck.deck_id, pick.label_id, evidence, build_candidates(similarities[i], self.rows)))
        return predictions

    def state(self) -> dict[str, JSON]:
        """Which embedding, exactly, and what fitting found about its inputs; never the vectors, which the embedding and the training decks rebuild."""
        return {'embedding': self.params['embedding'], 'embedding_hash': self.embedding_hash, 'training_decks': self.training_decks, 'training_rows': len(self.rows.labels),
                'skipped_copies': self.skipped_copies, 'decks_with_skipped_cards': self.decks_with_skipped_cards, 'skipped_cards': dict(self.skipped_cards)}

    @classmethod
    def from_state(cls, params: dict[str, JSON], state: dict[str, JSON], training: Sequence[TrainingDeck], context: FitContext) -> 'EmbeddingNearestDeck':
        """Reloads the embedding, refusing one that changed since fitting, and rebuilds the rows from the training decks."""
        model = cls(params)
        model.load_embedding(context)
        if model.embedding_hash != state['embedding_hash']:
            raise ValueError(f'The embedding {params["embedding"]} has changed since the model was fitted: it was {state["embedding_hash"]}, it is now {model.embedding_hash}')
        model.build_index(training)
        model.training_decks = cast(int, state['training_decks'])
        model.skipped_copies = cast(int, state['skipped_copies'])
        model.decks_with_skipped_cards = cast(int, state['decks_with_skipped_cards'])
        model.skipped_cards = cast(dict[str, int], state['skipped_cards'])
        return model
