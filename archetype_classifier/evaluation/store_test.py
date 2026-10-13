import hashlib
import math

from archetype_classifier.evaluation.model import Candidate, Prediction
from archetype_classifier.evaluation.store import candidates_json, clean_candidates, prediction_hash

RED_DECK_WINS, AZORIUS_CONTROL, PRISONER = 16, 49, 222


# Scenario: a run stores one guess per deck, never scores (the prediction hash).

def test_the_prediction_hash_covers_every_guess_but_not_order_or_evidence() -> None:
    run = [Prediction(201, RED_DECK_WINS, {'n': 1}), Prediction(202, RED_DECK_WINS, {'n': 1}), Prediction(203, None, {})]
    assert prediction_hash(list(reversed(run))) == prediction_hash(run)
    assert prediction_hash([Prediction(p.deck_id, p.guess_id, {'n': 2}) for p in run]) == prediction_hash(run)
    assert prediction_hash([run[0], Prediction(202, AZORIUS_CONTROL, {'n': 1}), run[2]]) != prediction_hash(run)
    assert prediction_hash([run[0], run[1], Prediction(203, RED_DECK_WINS, {})]) != prediction_hash(run)  # No guess differs from a guess.
    assert prediction_hash(run[:2]) != prediction_hash(run)


# Ranked candidates (#14): tests only, as agreed, not scenarios.

def test_a_run_without_candidates_keeps_its_hash() -> None:
    run = [Prediction(201, RED_DECK_WINS, {}), Prediction(203, None, {})]
    assert prediction_hash(run) == hashlib.sha1(b'201:16;203:-1').hexdigest()  # As runs 1-6 were hashed.

def test_the_prediction_hash_covers_candidates_and_their_scores() -> None:
    ranked = [Prediction(201, RED_DECK_WINS, {}, (Candidate(RED_DECK_WINS, 0.9), Candidate(PRISONER, 0.8)))]
    reordered = [Prediction(201, RED_DECK_WINS, {}, (Candidate(PRISONER, 0.8), Candidate(RED_DECK_WINS, 0.9)))]
    rescored = [Prediction(201, RED_DECK_WINS, {}, (Candidate(RED_DECK_WINS, 0.9), Candidate(PRISONER, 0.7)))]
    empty = [Prediction(201, RED_DECK_WINS, {}, ())]
    unranked = [Prediction(201, RED_DECK_WINS, {})]
    assert len({prediction_hash(run) for run in (ranked, reordered, rescored, empty, unranked)}) == 5
    assert prediction_hash([Prediction(201, RED_DECK_WINS, {}, (Candidate(RED_DECK_WINS, 0.90001), Candidate(PRISONER, 0.8)))]) == prediction_hash(ranked)  # Hashed as stored, to 4 decimals.

def test_candidates_are_stored_as_compact_json_pairs_to_4_decimals() -> None:
    assert candidates_json((Candidate(42, 0.812345), Candidate(17, 64), Candidate(9, math.nan), Candidate(8, None))) == '[[42,0.8123],[17,64],[9,null],[8,null]]'
    assert candidates_json(()) == '[]'
    assert candidates_json(None) is None

def test_a_clean_list_passes_unchanged_whatever_its_length() -> None:
    for candidates in [(), (Candidate(RED_DECK_WINS, 64),), (Candidate(RED_DECK_WINS, 64), Candidate(PRISONER, 64), Candidate(AZORIUS_CONTROL, 12))]:
        assert clean_candidates(candidates, frozenset({RED_DECK_WINS, PRISONER, AZORIUS_CONTROL})) == (candidates, frozenset())

def test_a_duplicated_archetype_keeps_its_first_position() -> None:
    candidates = (Candidate(RED_DECK_WINS, 0.9), Candidate(PRISONER, 0.8), Candidate(RED_DECK_WINS, 0.7), Candidate(AZORIUS_CONTROL, 0.6))
    assert clean_candidates(candidates, frozenset({RED_DECK_WINS, PRISONER, AZORIUS_CONTROL})) == (
        (Candidate(RED_DECK_WINS, 0.9), Candidate(PRISONER, 0.8), Candidate(AZORIUS_CONTROL, 0.6)), frozenset({'a duplicated archetype'}))

def test_an_id_outside_the_tree_stays_in_place() -> None:
    candidates = (Candidate(999, 0.9), Candidate(RED_DECK_WINS, 0.8))
    assert clean_candidates(candidates, frozenset({RED_DECK_WINS})) == (candidates, frozenset({'an archetype not in the tree'}))

def test_scores_out_of_order_keep_the_models_ranking() -> None:
    candidates = (Candidate(PRISONER, 0.61), Candidate(RED_DECK_WINS, 0.83), Candidate(AZORIUS_CONTROL, 0.40))
    assert clean_candidates(candidates, frozenset({RED_DECK_WINS, PRISONER, AZORIUS_CONTROL})) == (candidates, frozenset({'scores out of order'}))

def test_a_nan_score_becomes_no_score() -> None:
    candidates = (Candidate(RED_DECK_WINS, 0.9), Candidate(PRISONER, math.nan), Candidate(AZORIUS_CONTROL, 0.95))
    assert clean_candidates(candidates, frozenset({RED_DECK_WINS, PRISONER, AZORIUS_CONTROL})) == (
        (Candidate(RED_DECK_WINS, 0.9), Candidate(PRISONER, None), Candidate(AZORIUS_CONTROL, 0.95)), frozenset({'a NaN score', 'scores out of order'}))
