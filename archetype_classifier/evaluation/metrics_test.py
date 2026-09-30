from pytest import approx

from archetype_classifier.evaluation.metrics import score_deck
from archetype_classifier.evaluation.scenario_set import AGGRO, AZORIUS_CONTROL, MONO_RED_DEVOTION, NO_GUESS, PRISONER, RED_DECK_WINS, TREE

THREE_PLACES = 0.0005  # Scenarios.md gives scores to three decimal places.


def test_an_exact_guess_scores_one() -> None:
    s = score_deck(TREE, PRISONER, PRISONER)
    assert (s.hp, s.hr, s.hf) == (1.0, 1.0, 1.0)
    assert s.exact

def test_a_correct_parent_fallback_beats_a_wrong_branch() -> None:
    guesses = [PRISONER, RED_DECK_WINS, MONO_RED_DEVOTION, AZORIUS_CONTROL]
    scores = [score_deck(TREE, PRISONER, guess) for guess in guesses]
    assert [(s.hp, s.hr) for s in scores] == [approx((1.0, 1.0), abs=THREE_PLACES), approx((1.0, 0.667), abs=THREE_PLACES), approx((0.667, 0.667), abs=THREE_PLACES), (0.0, 0.0)]
    hfs = [s.hf for s in scores]
    assert hfs == sorted(hfs, reverse=True) and len(set(hfs)) == 4

def test_a_too_specific_guess_on_a_parent_label_is_penalised() -> None:
    too_specific = score_deck(TREE, RED_DECK_WINS, PRISONER)
    assert (too_specific.hp, too_specific.hr) == approx((0.667, 1.0), abs=THREE_PLACES)
    assert score_deck(TREE, RED_DECK_WINS, RED_DECK_WINS).hf > too_specific.hf > score_deck(TREE, RED_DECK_WINS, AZORIUS_CONTROL).hf
    # Tentative: a too-specific guess costs more precision than a parent fallback the same distance off.
    assert too_specific.hp < score_deck(TREE, PRISONER, RED_DECK_WINS).hp

def test_a_wrong_child_on_the_right_branch_beats_a_top_level_fallback() -> None:
    assert score_deck(TREE, PRISONER, MONO_RED_DEVOTION).hf == approx(0.667, abs=THREE_PLACES)
    assert score_deck(TREE, PRISONER, AGGRO).hf == approx(0.5, abs=THREE_PLACES)

def test_no_guess_scores_as_a_guess_of_the_root() -> None:
    s = score_deck(TREE, PRISONER, NO_GUESS)
    assert (s.hp, s.hr, s.hf) == (None, 0.0, 0.0)
    assert not s.exact
