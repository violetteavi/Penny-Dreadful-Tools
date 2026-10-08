"""The nearest deck on the combined embedding, on rule-level decks (Scenarios.md, "The nearest deck on the combined embedding"). Real data is checked in
embedding_nearest_local_test.py."""
import numpy as np

from archetype_classifier.card_embeddings.deck_vectors_test import cards
from archetype_classifier.data_loading.dataset import CardCount
from archetype_classifier.data_loading.labels import LabelStatus
from archetype_classifier.evaluation.model import PredictDeck, TrainingDeck
from archetype_classifier.models.embedding_nearest import build_training_rows

AGGRO, CONTROL, RED_DECK_WINS, BURN, AZORIUS_CONTROL = 1, 2, 16, 17, 49
MAINDECK_A = cards(Shock=4, Burst_Lightning=4, Mountain=52)
MAINDECK_B = cards(Essence_Scatter=4, Negate=4, Island=52)


def training(deck_id: int, archetype_id: int | None, maindeck: tuple[CardCount, ...], sideboard: tuple[CardCount, ...] = ()) -> TrainingDeck:
    return TrainingDeck(PredictDeck(deck_id, 'League', maindeck, sideboard), 30, archetype_id, True, LabelStatus.VERIFIED)

TRAINING = [training(101, RED_DECK_WINS, MAINDECK_A), training(103, RED_DECK_WINS, MAINDECK_A, sideboard=cards(Negate=4)), training(105, BURN, MAINDECK_A),
            training(107, AZORIUS_CONTROL, MAINDECK_B)]


# Scenario: repeated maindecks are one training row.

def test_repeated_maindecks_are_one_training_row() -> None:
    rows = build_training_rows(TRAINING)
    assert list(zip(rows.maindecks, rows.labels.tolist(), rows.deck_counts.tolist(), rows.newest_deck_ids.tolist())) == [
        (MAINDECK_A, RED_DECK_WINS, 2, 103), (MAINDECK_A, BURN, 1, 105), (MAINDECK_B, AZORIUS_CONTROL, 1, 107)]

def test_a_training_deck_with_no_label_is_skipped() -> None:
    rows = build_training_rows([*TRAINING, training(109, None, MAINDECK_B)])
    assert rows.deck_counts.tolist() == [2, 1, 1]

def test_no_training_decks_give_no_rows() -> None:
    rows = build_training_rows([])
    assert (rows.maindecks, len(rows.labels)) == ((), 0)
    assert rows.labels.dtype == np.int64
