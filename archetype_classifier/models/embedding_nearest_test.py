"""The nearest deck on the combined embedding, on rule-level decks (Scenarios.md, "The nearest deck on the combined embedding"). Real data is checked in
embedding_nearest_local_test.py."""
import numpy as np
import pytest

from archetype_classifier.card_embeddings.deck_vectors_test import cards
from archetype_classifier.data_loading.dataset import CardCount
from archetype_classifier.data_loading.labels import LabelStatus
from archetype_classifier.evaluation.model import PredictDeck, TrainingDeck
from archetype_classifier.models.embedding_nearest import Pick, build_pick, build_training_rows

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


# Scenario: a tie goes to the label with more decks, then to the newer deck. Rows: 1 = A Red Deck Wins (2 decks, newest 103), 2 = A Burn (1, 105),
# 3 = B Azorius Control (1, 107).

ROWS = build_training_rows(TRAINING)

@pytest.mark.parametrize(('similarities', 'pick'), [
    ([1.0, 1.0, 0.91], Pick(RED_DECK_WINS, 103, 1.0, 2, 2, BURN, 1.0)),  # A tie between two labels: 2 decks beat 1.
    ([1.0, 1.0 - 1e-10, 0.91], Pick(RED_DECK_WINS, 103, 1.0, 2, 2, BURN, 1.0 - 1e-10)),  # Within the tolerance: still tied.
    ([1.0 - 1e-8, 1.0, 0.91], Pick(BURN, 105, 1.0, 1, 1, RED_DECK_WINS, 1.0 - 1e-8)),  # Just outside it: row 2 alone is best.
    ([0.5, 0.2, 0.97], Pick(AZORIUS_CONTROL, 107, 0.97, 1, 1, RED_DECK_WINS, 0.5)),  # A near one-deck row beats the far popular one.
])
def test_the_pick_rule(similarities: list[float], pick: Pick) -> None:
    assert build_pick(np.array(similarities), ROWS) == pick

def test_equal_decks_go_to_the_newer_deck() -> None:
    rows = build_training_rows([training(101, RED_DECK_WINS, MAINDECK_A), training(105, BURN, MAINDECK_A), training(107, AZORIUS_CONTROL, MAINDECK_B)])
    assert build_pick(np.array([1.0, 1.0, 0.91]), rows) == Pick(BURN, 105, 1.0, 1, 2, RED_DECK_WINS, 1.0)

def test_with_no_other_label_there_is_no_runner_up() -> None:
    rows = build_training_rows([training(101, RED_DECK_WINS, MAINDECK_A), training(103, RED_DECK_WINS, MAINDECK_A), training(107, RED_DECK_WINS, MAINDECK_B)])
    assert build_pick(np.array([1.0, 0.91]), rows) == Pick(RED_DECK_WINS, 103, 1.0, 2, 1, None, None)
