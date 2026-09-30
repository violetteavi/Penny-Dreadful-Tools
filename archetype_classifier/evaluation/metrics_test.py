import pytest
from pytest import approx

from archetype_classifier.evaluation.metrics import score, score_deck
from archetype_classifier.evaluation.scenario_set import AGGRO, AZORIUS_CONTROL, MONO_RED_DEVOTION, NO_GUESS, PRISONER, RED_DECK_WINS, TREE, scenario_decks

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

P, MRD, RDW, A, AC, NONE = PRISONER, MONO_RED_DEVOTION, RED_DECK_WINS, AGGRO, AZORIUS_CONTROL, NO_GUESS
ON, OFF = True, False
# The table under "Summarising a set of guesses": label, guess, hP, hR, hF, depth difference, on-path.
SCENARIO_TABLE = [
    (P, P, 1.0, 1.0, 1.0, 0, ON), (P, MRD, 0.667, 0.667, 0.667, 0, OFF), (P, RDW, 1.0, 0.667, 0.8, -1, ON),
    (P, A, 1.0, 0.333, 0.5, -2, ON), (P, AC, 0.0, 0.0, 0.0, -1, OFF), (P, NONE, None, 0.0, 0.0, -3, ON),
    (MRD, P, 0.667, 0.667, 0.667, 0, OFF), (MRD, MRD, 1.0, 1.0, 1.0, 0, ON), (MRD, RDW, 1.0, 0.667, 0.8, -1, ON),
    (MRD, A, 1.0, 0.333, 0.5, -2, ON), (MRD, AC, 0.0, 0.0, 0.0, -1, OFF), (MRD, NONE, None, 0.0, 0.0, -3, ON),
    (RDW, P, 0.667, 1.0, 0.8, 1, ON), (RDW, MRD, 0.667, 1.0, 0.8, 1, ON), (RDW, RDW, 1.0, 1.0, 1.0, 0, ON),
    (RDW, A, 1.0, 0.5, 0.667, -1, ON), (RDW, AC, 0.0, 0.0, 0.0, 0, OFF), (RDW, NONE, None, 0.0, 0.0, -2, ON),
    (A, P, 0.333, 1.0, 0.5, 2, ON), (A, MRD, 0.333, 1.0, 0.5, 2, ON), (A, RDW, 0.5, 1.0, 0.667, 1, ON),
    (A, A, 1.0, 1.0, 1.0, 0, ON), (A, AC, 0.0, 0.0, 0.0, 1, OFF), (A, NONE, None, 0.0, 0.0, -1, ON),
    (AC, P, 0.0, 0.0, 0.0, 1, OFF), (AC, MRD, 0.0, 0.0, 0.0, 1, OFF), (AC, RDW, 0.0, 0.0, 0.0, 0, OFF),
    (AC, A, 0.0, 0.0, 0.0, -1, OFF), (AC, AC, 1.0, 1.0, 1.0, 0, ON), (AC, NONE, None, 0.0, 0.0, -2, ON),
]

@pytest.mark.parametrize(('label', 'guess', 'hp', 'hr', 'hf', 'depth_difference', 'on_path'), SCENARIO_TABLE)
def test_every_pair_in_the_scenario_table_scores_as_listed(label: int, guess: int | None, hp: float | None, hr: float, hf: float, depth_difference: int, on_path: bool) -> None:
    s = score_deck(TREE, label, guess)
    assert s.hp == (None if hp is None else approx(hp, abs=THREE_PLACES))
    assert (s.hr, s.hf) == approx((hr, hf), abs=THREE_PLACES)
    assert (s.depth_difference, s.on_path) == (depth_difference, on_path)

def test_micro_averaging_sums_over_decks() -> None:
    micro = score(TREE, scenario_decks()).micro
    assert (micro.hp, micro.hr, micro.hf) == approx((0.911, 0.865, 0.887), abs=THREE_PLACES)

def test_coverage_and_exact_match_rate() -> None:
    scores = score(TREE, scenario_decks())
    assert scores.coverage == approx(4110 / 4350)
    assert scores.exact_match_rate == approx(3000 / 4350)
