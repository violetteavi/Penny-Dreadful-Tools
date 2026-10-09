"""The nearest deck on the combined embedding, on rule-level decks (Scenarios.md, "The nearest deck on the combined embedding"). Real data is checked in
embedding_nearest_local_test.py."""
from pathlib import Path

import numpy as np
import pytest

from archetype_classifier.card_embeddings.combined_embedding import load_embedding_hash, save_combined_embedding
from archetype_classifier.card_embeddings.deck_vectors_test import EMBEDDING, cards
from archetype_classifier.data_loading.dataset import ArchetypeSnapshot, CardCount
from archetype_classifier.data_loading.labels import LabelStatus
from archetype_classifier.evaluation.metrics import ArchetypeTree
from archetype_classifier.evaluation.model import FitContext, PredictDeck, Prediction, TrainingDeck, model_class
from archetype_classifier.models.embedding_nearest import EmbeddingNearestDeck, Pick, build_pick, build_training_rows

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


# The model through the Model protocol, on the small embedding saved to a temporary folder.

TREE = ArchetypeTree({AGGRO: ArchetypeSnapshot(AGGRO, 'Aggro', None, 0), CONTROL: ArchetypeSnapshot(CONTROL, 'Control', None, 0),
                      RED_DECK_WINS: ArchetypeSnapshot(RED_DECK_WINS, 'Red Deck Wins', AGGRO, 1), BURN: ArchetypeSnapshot(BURN, 'Burn', AGGRO, 1),
                      AZORIUS_CONTROL: ArchetypeSnapshot(AZORIUS_CONTROL, 'Azorius Control', CONTROL, 1)})

@pytest.fixture
def embedding_path(tmp_path: Path) -> Path:
    return save_combined_embedding(EMBEDDING, tmp_path)

def context(path: Path) -> FitContext:
    return FitContext(TREE, {}, seed=0, embeddings_dir=path.parent)

def fitted(path: Path, training: list[TrainingDeck] = TRAINING) -> EmbeddingNearestDeck:
    model = EmbeddingNearestDeck({'embedding': path.stem})
    model.fit(training, [], context(path))
    return model

def query(deck_id: int, maindeck: tuple[CardCount, ...], sideboard: tuple[CardCount, ...] = ()) -> PredictDeck:
    return PredictDeck(deck_id, 'League', maindeck, sideboard)

def test_the_model_is_found_by_its_name() -> None:
    assert model_class('embedding nearest deck') is EmbeddingNearestDeck

def test_a_deck_identical_to_training_decks_copies_the_label_with_more_decks(embedding_path: Path) -> None:
    [prediction] = fitted(embedding_path).predict([query(201, MAINDECK_A)])
    assert prediction == Prediction(201, RED_DECK_WINS, {'match_deck_id': 103, 'similarity': 1.0, 'match_decks': 2, 'tied_rows': 2, 'runner_up_id': BURN,
                                                         'runner_up_similarity': 1.0, 'embedded_copies': 60, 'skipped_copies': 0})

def test_the_sideboard_never_changes_a_guess(embedding_path: Path) -> None:
    model = fitted(embedding_path)
    without, with_sideboard = model.predict([query(201, MAINDECK_B), query(201, MAINDECK_B, sideboard=cards(Shock=4, Mountain=11))])
    assert without == with_sideboard
    assert without.guess_id == AZORIUS_CONTROL

def test_a_deck_of_only_missing_cards_gets_no_guess(embedding_path: Path) -> None:
    [prediction] = fitted(embedding_path).predict([query(202, cards(Smaug_s_Fury=60))])
    assert prediction == Prediction(202, None, {'embedded_copies': 0, 'skipped_copies': 60})

def test_with_no_training_rows_no_deck_gets_a_guess(embedding_path: Path) -> None:
    [prediction] = fitted(embedding_path, [training(109, None, MAINDECK_A)]).predict([query(201, MAINDECK_A)])
    assert prediction == Prediction(201, None, {'embedded_copies': 60, 'skipped_copies': 0})


# Scenarios: a card missing from the embedding is skipped and counted; a fitted model loads back, and refuses a changed embedding.

def test_the_state_records_the_embedding_and_the_skipped_cards_never_vectors(embedding_path: Path) -> None:
    with_missing = [*TRAINING, training(111, BURN, cards(Shock=4, Mountain=52, Smaug_s_Fury=4)), training(113, BURN, cards(Shock=4, Mountain=52, Smaug_s_Fury=4))]
    assert fitted(embedding_path, with_missing).state() == {
        'embedding': embedding_path.stem, 'embedding_hash': load_embedding_hash(embedding_path), 'training_decks': 6, 'training_rows': 4,
        'skipped_copies': 8, 'decks_with_skipped_cards': 2, 'skipped_cards': {"Smaug's Fury": 8}}

def test_a_fitted_model_loads_back_and_guesses_the_same(embedding_path: Path) -> None:
    model = fitted(embedding_path)
    decks = [query(201, MAINDECK_A), query(202, cards(Shock=4, Burst_Lightning=2, Mountain=54)), query(203, cards(Essence_Scatter=2, Negate=4, Island=54))]
    loaded = EmbeddingNearestDeck.from_state(model.params, model.state(), TRAINING, context(embedding_path))
    assert loaded.predict(decks) == model.predict(decks)
    assert loaded.state() == model.state()

def test_a_changed_embedding_is_refused_naming_both_hashes(embedding_path: Path) -> None:
    model = fitted(embedding_path)
    before = load_embedding_hash(embedding_path)
    json_file = embedding_path.with_suffix('.json')
    json_file.write_text(json_file.read_text() + ' ')
    with pytest.raises(ValueError, match=f'{before}.*{load_embedding_hash(embedding_path)}'):
        EmbeddingNearestDeck.from_state(model.params, model.state(), TRAINING, context(embedding_path))
