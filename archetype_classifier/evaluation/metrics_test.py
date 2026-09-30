from archetype_classifier.evaluation.metrics import score_deck
from archetype_classifier.evaluation.scenario_set import PRISONER, TREE


def test_an_exact_guess_scores_one() -> None:
    s = score_deck(TREE, PRISONER, PRISONER)
    assert (s.hp, s.hr, s.hf) == (1.0, 1.0, 1.0)
    assert s.exact
