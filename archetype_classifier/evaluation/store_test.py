from archetype_classifier.evaluation.model import Prediction
from archetype_classifier.evaluation.store import prediction_hash

RED_DECK_WINS, AZORIUS_CONTROL = 16, 49


# Scenario: a run stores one guess per deck, never scores (the prediction hash).

def test_the_prediction_hash_covers_every_guess_but_not_order_or_evidence() -> None:
    run = [Prediction(201, RED_DECK_WINS, {'n': 1}), Prediction(202, RED_DECK_WINS, {'n': 1}), Prediction(203, None, {})]
    assert prediction_hash(list(reversed(run))) == prediction_hash(run)
    assert prediction_hash([Prediction(p.deck_id, p.guess_id, {'n': 2}) for p in run]) == prediction_hash(run)
    assert prediction_hash([run[0], Prediction(202, AZORIUS_CONTROL, {'n': 1}), run[2]]) != prediction_hash(run)
    assert prediction_hash([run[0], run[1], Prediction(203, RED_DECK_WINS, {})]) != prediction_hash(run)  # No guess differs from a guess.
    assert prediction_hash(run[:2]) != prediction_hash(run)
