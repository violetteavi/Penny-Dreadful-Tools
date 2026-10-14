"""The nearest deck on the combined embedding, on rule-level decks (Scenarios.md, "The nearest deck on the combined embedding"). Real data is checked in
embedding_nearest_local_test.py."""
import dataclasses
import math
from pathlib import Path

import numpy as np
import pytest

from archetype_classifier.card_embeddings.combined_embedding import load_embedding_hash, save_combined_embedding
from archetype_classifier.card_embeddings.deck_vectors import build_deck_vectors
from archetype_classifier.card_embeddings.deck_vectors_test import EMBEDDING, cards
from archetype_classifier.data_loading.dataset import ArchetypeSnapshot, CardCount
from archetype_classifier.data_loading.labels import LabelStatus
from archetype_classifier.evaluation.metrics import ArchetypeTree
from archetype_classifier.evaluation.model import Candidate, FitContext, PredictDeck, Prediction, TrainingDeck, model_class
from archetype_classifier.models.card_weights import build_card_weights
from archetype_classifier.models.card_weights_test import LEGAL
from archetype_classifier.models.card_weights_test import TRAINING as WEIGHT_TRAINING
from archetype_classifier.models.embedding_nearest import EmbeddingNearestDeck, Pick, build_candidates, build_pick, build_training_rows

AGGRO, CONTROL, RED_DECK_WINS, MONO_RED_SWARM, AZORIUS_CONTROL = 1, 2, 16, 17, 49
MAINDECK_A = cards(Shock=4, Burst_Lightning=4, Mountain=52)
MAINDECK_B = cards(Essence_Scatter=4, Negate=4, Island=52)


def training(deck_id: int, archetype_id: int | None, maindeck: tuple[CardCount, ...], sideboard: tuple[CardCount, ...] = ()) -> TrainingDeck:
    return TrainingDeck(PredictDeck(deck_id, 'League', maindeck, sideboard), 30, archetype_id, True, LabelStatus.VERIFIED)

TRAINING = [training(101, RED_DECK_WINS, MAINDECK_A), training(103, RED_DECK_WINS, MAINDECK_A, sideboard=cards(Negate=4)), training(105, MONO_RED_SWARM, MAINDECK_A),
            training(107, AZORIUS_CONTROL, MAINDECK_B)]


# Scenario: repeated maindecks are one training row.

def test_repeated_maindecks_are_one_training_row() -> None:
    rows = build_training_rows(TRAINING)
    assert list(zip(rows.maindecks, rows.labels.tolist(), rows.deck_counts.tolist(), rows.newest_deck_ids.tolist())) == [
        (MAINDECK_A, RED_DECK_WINS, 2, 103), (MAINDECK_A, MONO_RED_SWARM, 1, 105), (MAINDECK_B, AZORIUS_CONTROL, 1, 107)]

def test_a_training_deck_with_no_label_is_skipped() -> None:
    rows = build_training_rows([*TRAINING, training(109, None, MAINDECK_B)])
    assert rows.deck_counts.tolist() == [2, 1, 1]

def test_no_training_decks_give_no_rows() -> None:
    rows = build_training_rows([])
    assert (rows.maindecks, len(rows.labels)) == ((), 0)
    assert rows.labels.dtype == np.int64


# Scenario: a tie goes to the label with more decks, then to the newer deck. Rows: 1 = A Red Deck Wins (2 decks, newest 103), 2 = A Mono Red Swarm (1, 105),
# 3 = B Azorius Control (1, 107).

ROWS = build_training_rows(TRAINING)

@pytest.mark.parametrize(('similarities', 'pick'), [
    ([1.0, 1.0, 0.91], Pick(RED_DECK_WINS, 103, 1.0, 2, 2, MONO_RED_SWARM, 1.0)),  # A tie between two labels: 2 decks beat 1.
    ([1.0, 1.0 - 1e-10, 0.91], Pick(RED_DECK_WINS, 103, 1.0, 2, 2, MONO_RED_SWARM, 1.0 - 1e-10)),  # Within the tolerance: still tied.
    ([1.0 - 1e-8, 1.0, 0.91], Pick(MONO_RED_SWARM, 105, 1.0, 1, 1, RED_DECK_WINS, 1.0 - 1e-8)),  # Just outside it: row 2 alone is best.
    ([0.5, 0.2, 0.97], Pick(AZORIUS_CONTROL, 107, 0.97, 1, 1, RED_DECK_WINS, 0.5)),  # A near one-deck row beats the far popular one.
])
def test_the_pick_rule(similarities: list[float], pick: Pick) -> None:
    assert build_pick(np.array(similarities), ROWS) == pick

def test_equal_decks_go_to_the_newer_deck() -> None:
    rows = build_training_rows([training(101, RED_DECK_WINS, MAINDECK_A), training(105, MONO_RED_SWARM, MAINDECK_A), training(107, AZORIUS_CONTROL, MAINDECK_B)])
    assert build_pick(np.array([1.0, 1.0, 0.91]), rows) == Pick(MONO_RED_SWARM, 105, 1.0, 1, 2, RED_DECK_WINS, 1.0)

def test_with_no_other_label_there_is_no_runner_up() -> None:
    rows = build_training_rows([training(101, RED_DECK_WINS, MAINDECK_A), training(103, RED_DECK_WINS, MAINDECK_A), training(107, RED_DECK_WINS, MAINDECK_B)])
    assert build_pick(np.array([1.0, 0.91]), rows) == Pick(RED_DECK_WINS, 103, 1.0, 2, 1, None, None)


# The model through the Model protocol, on the small embedding saved to a temporary folder.

TREE = ArchetypeTree({AGGRO: ArchetypeSnapshot(AGGRO, 'Aggro', None, 0), CONTROL: ArchetypeSnapshot(CONTROL, 'Control', None, 0),
                      RED_DECK_WINS: ArchetypeSnapshot(RED_DECK_WINS, 'Red Deck Wins', AGGRO, 1), MONO_RED_SWARM: ArchetypeSnapshot(MONO_RED_SWARM, 'Mono Red Swarm', AGGRO, 1),
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
    assert dataclasses.replace(prediction, candidates=None) == Prediction(201, RED_DECK_WINS, {
        'match_deck_id': 103, 'similarity': 1.0, 'match_decks': 2, 'tied_rows': 2, 'runner_up_id': MONO_RED_SWARM, 'runner_up_similarity': 1.0, 'embedded_copies': 60, 'skipped_copies': 0})
    assert prediction.candidates is not None
    assert [c.archetype_id for c in prediction.candidates] == [RED_DECK_WINS, MONO_RED_SWARM, AZORIUS_CONTROL]
    assert [c.score for c in prediction.candidates[:2]] == pytest.approx([1.0, 1.0])

def test_the_sideboard_never_changes_a_guess(embedding_path: Path) -> None:
    model = fitted(embedding_path)
    without, with_sideboard = model.predict([query(201, MAINDECK_B), query(201, MAINDECK_B, sideboard=cards(Shock=4, Mountain=11))])
    assert without == with_sideboard
    assert without.guess_id == AZORIUS_CONTROL

def test_a_deck_of_only_missing_cards_gets_no_guess(embedding_path: Path) -> None:
    [prediction] = fitted(embedding_path).predict([query(202, cards(Smaug_s_Fury=60))])
    assert prediction == Prediction(202, None, {'embedded_copies': 0, 'skipped_copies': 60}, ())  # The model ranks candidates, but has none for this deck.

def test_with_no_training_rows_no_deck_gets_a_guess(embedding_path: Path) -> None:
    [prediction] = fitted(embedding_path, [training(109, None, MAINDECK_A)]).predict([query(201, MAINDECK_A)])
    assert prediction == Prediction(201, None, {'embedded_copies': 60, 'skipped_copies': 0}, ())


# Scenarios: a card missing from the embedding is skipped and counted; a fitted model loads back, and refuses a changed embedding.

def test_the_state_records_the_embedding_and_the_skipped_cards_never_vectors(embedding_path: Path) -> None:
    with_missing = [*TRAINING, training(111, MONO_RED_SWARM, cards(Shock=4, Mountain=52, Smaug_s_Fury=4)), training(113, MONO_RED_SWARM, cards(Shock=4, Mountain=52, Smaug_s_Fury=4))]
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



# Scenario: the nearest deck ranks each label by its best training row (Scenarios.md, "Ranked candidates").

MAINDECK_C = cards(Burst_Lightning=4, Mountain=56)
RANKING = [*TRAINING, training(109, RED_DECK_WINS, MAINDECK_C)]  # Rows: 1 = A Red Deck Wins (2 decks, newest 103), 2 = A Mono Red Swarm (1, 105),
# 3 = B Azorius Control (1, 107), 4 = C Red Deck Wins (1, 109).
RED, SWARM, BLUE = RED_DECK_WINS, MONO_RED_SWARM, AZORIUS_CONTROL

@pytest.mark.parametrize(('training_decks', 'similarities', 'expected'), [
    (RANKING, [1.0, 1.0, 0.91, 0.70], [(RED, 1.0), (SWARM, 1.0), (BLUE, 0.91)]),  # A tie at the top: 2 decks beat 1.
    (RANKING, [0.80, 0.95, 0.91, 0.97], [(RED, 0.97), (SWARM, 0.95), (BLUE, 0.91)]),  # A label's best row decides.
    ([t for t in RANKING if t.deck.deck_id != 103], [1.0, 1.0, 0.91, 0.70], [(SWARM, 1.0), (RED, 1.0), (BLUE, 0.91)]),  # Equal decks: 105 is newer than 101.
    (RANKING, [0.99, 0.90, 0.90, 0.50], [(RED, 0.99), (BLUE, 0.90), (SWARM, 0.90)]),  # A tie below the top: 107 is newer than 105.
], ids=['tie at the top', 'best row decides', 'equal decks', 'tie below the top'])
def test_the_nearest_deck_ranks_each_label_by_its_best_training_row(training_decks: list[TrainingDeck], similarities: list[float], expected: list[tuple[int, float]]) -> None:
    rows = build_training_rows(training_decks)
    candidates = build_candidates(np.array(similarities), rows)
    assert candidates == tuple(Candidate(a, s) for a, s in expected)
    assert candidates[0].archetype_id == build_pick(np.array(similarities), rows).label_id

def test_with_no_training_rows_there_are_no_candidates() -> None:
    assert build_candidates(np.array([]), build_training_rows([])) == ()

def test_candidate_1_is_always_the_guess_on_random_similarities() -> None:
    rng = np.random.default_rng(0)
    decks = [training(200 + i, int(rng.choice([RED, SWARM, BLUE, AGGRO, CONTROL])), (CardCount('Mountain', i + 1),)) for i in range(40)]
    rows = build_training_rows(decks + decks[:15])  # Repeats make deck counts differ.
    for _ in range(300):
        similarities = rng.choice([0.2, 0.5, 0.5 + 1e-10, 0.8, 1.0], size=len(rows.labels))  # Few values, so ties are common.
        candidates = build_candidates(similarities, rows)
        assert candidates[0].archetype_id == build_pick(similarities, rows).label_id
        assert sorted(c.archetype_id for c in candidates) == sorted(set(rows.labels.tolist()))
        scores = [c.score for c in candidates]
        assert all(later is not None and earlier is not None and later <= earlier + 1e-9 for earlier, later in zip(scores, scores[1:]))

def test_version_3_weighs_cards() -> None:
    assert EmbeddingNearestDeck.version == 3


# Card weights and copies (#50; Scenarios.md, "Deck representations"), on the card-weight scenario's training decks.

def weighted(path: Path, legal: dict[int, frozenset[str]] = LEGAL, **params: str) -> EmbeddingNearestDeck:
    model = EmbeddingNearestDeck({'embedding': path.stem, **params})
    model.fit(WEIGHT_TRAINING, [], FitContext(TREE, legal, seed=0, embeddings_dir=path.parent))
    return model

def test_unknown_weights_or_copies_are_refused() -> None:
    with pytest.raises(ValueError, match="weights must be one of"):
        EmbeddingNearestDeck({'embedding': 'e', 'weights': 'tf-idf'})
    with pytest.raises(ValueError, match="copies must be one of"):
        EmbeddingNearestDeck({'embedding': 'e', 'copies': 'log'})

def test_no_weights_and_linear_copies_are_version_2s_model(embedding_path: Path) -> None:
    default, explicit = fitted(embedding_path), weighted(embedding_path, weights='none', copies='linear')
    explicit.fit(TRAINING, [], context(embedding_path))
    decks = [query(201, MAINDECK_A), query(202, cards(Shock=4, Burst_Lightning=2, Mountain=54)), query(203, cards(Essence_Scatter=2, Negate=4, Island=54))]
    assert explicit.predict(decks) == default.predict(decks)
    assert 'card_weights' not in default.state()

def test_rows_and_decks_are_read_with_card_weights_and_square_root_copies(embedding_path: Path) -> None:
    model = weighted(embedding_path, weights='idf', copies='sqrt')
    weights = build_card_weights(WEIGHT_TRAINING, LEGAL)
    assert np.allclose(model.row_vectors, build_deck_vectors(model.rows.maindecks, EMBEDDING, weights.weight, math.sqrt).matrix)
    [prediction] = model.predict([query(201, cards(Shock=4, Mountain=56))])
    assert prediction.evidence['similarity'] == pytest.approx(1.0)  # Read the same way as its identical training row.
    assert model.state()['card_weights'] == weights.summary()

def test_a_weighted_model_loads_back_and_guesses_the_same(embedding_path: Path) -> None:
    model = weighted(embedding_path, weights='idf', copies='sqrt')
    decks = [query(201, cards(Shock=4, Burst_Lightning=4, Mountain=52)), query(202, cards(Essence_Scatter=4, Negate=4, Island=52))]
    loaded = EmbeddingNearestDeck.from_state(model.params, model.state(), WEIGHT_TRAINING, FitContext(TREE, LEGAL, seed=0, embeddings_dir=embedding_path.parent))
    assert loaded.predict(decks) == model.predict(decks)
    assert loaded.state() == model.state()

def test_changed_card_weights_are_refused_naming_both_hashes(embedding_path: Path) -> None:
    model = weighted(embedding_path, weights='idf', copies='sqrt')
    changed = {30: LEGAL[30], 31: LEGAL[31] - {'Divination'}}
    before, after = build_card_weights(WEIGHT_TRAINING, LEGAL).hash(), build_card_weights(WEIGHT_TRAINING, changed).hash()
    with pytest.raises(ValueError, match=f'card weights.*{before}.*{after}'):
        EmbeddingNearestDeck.from_state(model.params, model.state(), WEIGHT_TRAINING, FitContext(TREE, changed, seed=0, embeddings_dir=embedding_path.parent))
